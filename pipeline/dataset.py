import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 
from dateutil import parser

from .utils import get_header
from .outlier import *

from datetime import datetime, timedelta
from statistics import mean
from math import isnan

class Dataset:
    def __init__(self, location):

        header, unit = get_header(location) #Get row number of header. If detected, also row number of unit row
        self.df = pd.read_csv(location, header=header) #This needs to be smarter (header=2 is not general enough)

        self.units = {}
        self.time_format = None
        self.sampling_rate = None
        self.average = None
        self.std_dev = None
        self.outliers = {}
        self.outliers_flagged = {}
        self.unit_flags = {}

        if(unit):
            tmp = self.df.iloc[0].values
            self.df = self.df.iloc[1:]
            if(len(tmp)==len(self.df.columns)):
                for i in range(len(tmp)):
                    self.units[self.df.columns[i]] = tmp[i]

    def scan_columns(self):
        columns = self.df.columns
        for i in range(len(columns)):
            name = columns[i]
            if('quality' in name):
                rows = self.df[name].to_numpy()
                if(i != 0):
                    related_col = columns[i-1]
                    print('Found column \'{0}\' which belongs to \'{1}\' and indicates missing values'.format(name, related_col))
                    flags = self.df[name].to_numpy()
                    counter = 0
                    for i in range(len(flags)):
                        try:
                            isnan(flags[i])
                        except TypeError:
                            self.df[related_col].iloc[i] = float('NaN')
                            counter += 1
                    print('Column: \'{0}\': {1} values have been replaced with nan'.format(related_col, counter))
                    self.df.drop(columns = name, inplace=True)
                    print('Dropped column \'{0}\''.format(name))
                else:
                    continue
            elif('unit' in name):
                rows = self.df[name].to_numpy()
                if(i!=0):
                    related_col = columns[i-1]
                    print('Found column \'{0}\' which belongs to \'{1}\' and indicates the corrsesponding unit'.format(name, related_col))
                    self.unit_flags[related_col] = self.df[name]
                    self.df.drop(columns = name, inplace=True)
                    print('Dropped column \'{0}\' and saved for later'.format(name))
                else:
                    continue
            
    def infer_format(self): #ToDo: Functionality to differentiate between US and EU format.
        #Name of first column (supposed to be time column)
        self.name_time = self.df.columns[0]
        
        #Get first and last (correct) timestamp
        first_stamp = parser.parse(self.df.iloc[0,0])
        last_stamp = parser.parse(self.df.iloc[-1,0])

        diff = last_stamp - first_stamp

        base_format = '%H:%M:%S'
        time_format = base_format

        if(diff.days >= 1):
            time_format =  '%Y-%m-%d ' + base_format

        self.time_format = time_format
        print('Chosen format: {0}'.format(time_format))

    def apply_format(self):
        next_idx = 0
        group = 0

        arr = self.df[self.name_time].to_numpy()
        counter = 0
        
        for i in range(len(arr)):
            val = arr[i]
            
            try:
                val = parser.parse(val)
                val = val.strftime(self.time_format)
                next_idx += 1

            #except TypeError as e:
                #If its already NaT
                
            except ValueError:
                counter += 1
                if next_idx == i:
                    next_idx = i+1
                else:
                    group = group + 1
                
                #print("Wrong val: {0}; Replaced with {1}".format(val, hex(group)))
                val = hex(group)
                
            arr[i] = val

        self.df[self.name_time]=arr  
        print('{0} timestamps could not be parsed and will be inferred later on'.format(counter))          
        #return self.df

    def clean_stamps(self):
        
        #Drop Duplicates first
        self.df = self.df.drop_duplicates()
        self.df.reset_index(drop=True, inplace=True)
        
        #Get List of all duplicated indices
        df_i_dup = self.df[self.df.duplicated(subset=[self.name_time],keep=False)]
        unique_dup = df_i_dup[self.name_time].unique() #[11:01:00, 0x0, 0x1]
        print('Recurring timestamps that need to be cleaned: {0}'.format(unique_dup))

        for idx,i in enumerate(unique_dup):
            print('Changing duplicate timestamps {0}'.format(i))
            
            tmp_df_i_dup = df_i_dup.loc[df_i_dup[self.name_time] == unique_dup[idx]] #Get list of specific duplicated indices
            
            n = len(tmp_df_i_dup)    
            
            dup_index = tmp_df_i_dup[~tmp_df_i_dup.duplicated(subset=[self.name_time],keep='first')].index[0]

            after = self.df.iloc[dup_index+n][self.name_time]
            after = parser.parse(after)

            before = self.df.iloc[dup_index-1][self.name_time]
            before = parser.parse(before)
            
            #Get diff between next actual timestep and first duplicate timestep
            diff = after - before
            diff /= (n+1)
            
            #Replace every duplicate timestamp with best possible value
            before_stamp = self.df.iloc[dup_index-1,0]
            before_stamp = parser.parse(before_stamp)
            for y in range(len(tmp_df_i_dup)):
                curr_stamp = before_stamp + (y+1)*diff
                curr_stamp = curr_stamp.strftime(self.time_format)
                
                self.df.iloc[dup_index+y,0] = curr_stamp
                #print(df.iloc[dup_index+y,0])
        
        #return self.df
    
    def time_as_index(self):
        if(not isinstance(self.df.index, pd.DatetimeIndex)):
            self.df[self.name_time] = pd.to_datetime(self.df[self.name_time], infer_datetime_format=True)
            self.df = self.df.set_index(self.name_time)
            try:
                del self.units[self.name_time]
            except KeyError:
                pass
            return True
        else:
            print('Index already datetime')
            return True
        
        return False #Maybe not needed

    def median_sampling_rate(self):
        median = None
        if(self.time_as_index()):
            values = self.df.index.to_series().diff()
            print('Sampling rates in the dataset: \n{0}'.format(values.value_counts()))
            median = values.median()
            print('Median: {0}'.format(median))
        
        return median

    def resample(self):
        #Prepare dummy dataframe with equidistant sampling rate
        freq = self.median_sampling_rate()
        cols = self.df.columns
        start = self.df.index.to_series().iloc[0]
        end = self.df.index.to_series().iloc[-1]

        index_dummy = pd.date_range(start=start, end=end, freq=freq)
        df_dummy = pd.DataFrame(index=index_dummy, columns=cols)

        #Concat dummy with df and drop duplicates
        self.df = pd.concat([self.df, df_dummy])
        self.df = self.df[~self.df.index.duplicated(keep='first')]
        self.df = self.df.sort_index()

        #Log amount of rows added for resampling
        df_tmp = pd.concat([self.df,self.df.dropna(how='all')])
        df_tmp = df_tmp[~df_tmp.index.duplicated(keep=False)]
        print('{0} rows were added due to resampling'.format(len(df_tmp)))

    def convert_na(self):
        cols = self.df.columns
        for i in range(len(cols)):
            if(self.df.dtypes[i]=='object'):
                self.df[cols[i]] = pd.to_numeric(self.df[cols[i]], errors='coerce')
                print('Converted column: \'{0}\' to numeric'.format(cols[i]))
    
    def interpolate(self, method='time', limit=0.2):
        limit = int(len(self.df)*0.2)
        na_rows = len(self.df[self.df.isnull().any(axis=1)])
        print('Before interpolation {0} rows contain nan values'.format(na_rows))
        self.df = self.df.interpolate(method=method, limit=limit).ffill().bfill()
        na_rows = len(self.df[self.df.isnull().any(axis=1)])
        print('After interpolation {0} rows contain nan values'.format(na_rows))
        if(na_rows>0):
            print('These rows might not have been filled due to exceeding the limit\n \
                Consider dropping these columns') 

    def drop_dup_cols(self):
        redundant = []
        for i in range(len(self.df.columns)-1):
            col = self.df.columns[i]
            arr = self.df[col].to_numpy()
        
            for y in range(i+1, len(self.df.columns)):
                col2 = self.df.columns[y]
                arr2 = self.df[col2].to_numpy()
                
                if(np.array_equal(arr, arr2)):
                    print('{0} {1} are equal'.format(col, col2))
                    redundant.append(col2)
        
        for i in range(len(redundant)):
            self.df.drop(columns = redundant[i], inplace=True)
            del self.units[redundant[i]]
            print('Column: \'{0}\' was dropped'.format(redundant[i]))
    
    def flag_outliers(self,col, dct):
        col, name = self.__check_col(col)
        if(not name):
            return
        
        try:
            dct[name]
            print('Flag outliers using multivariate outlier detection (this column correlates with other columns)')
            print('Detected outliers are marked with red and green.\nGreen: outliers not marked for cleaning\nRed: outliers marked for cleaning')
            self.flag_multivariate_outliers(col)
        except KeyError:
            print('Flag outliers using univariate outliers')
            print('Detected outliers are marked with red and green.\nGreen: outliers not marked for cleaning\nRed: outliers marked for cleaning')
            self.flag_univariate_outliers(col)

    def flag_multivariate_outliers(self,col):
        col, name = self.__check_col(col)
        if(not name):
            return
        
        try:
            corr = high_correlators(self.df, 0.7)[name]
        except KeyError:
            print('Column does not correlate enough with other columns to detect multivariate outliers')
            return
        
        lst = [name]
        lst.extend(corr)
        df = self.df[lst] #Get Dataframe with only this column and the correlating columns
        
        #Only caculate outliers if not already available
        outliers_mahal, md = mahalanobis_method(df=df)
        if(not outliers_mahal):
            print('No outliers found')
            return
        groups = group_outliers(outliers_mahal)
        #groups = extend_outliers(groups)
        self.outliers[name] = groups

        ax = col.plot()
        ax = visualize_outliers(col, ax, groups, color='green')

        means = []
        for i in range(len(groups)):
            subseries = col.iloc[groups[i][0]-1:groups[i][-1]]
            means.append(subseries.mean())
        
        pot_err = zscore_method(means,1)
        pot_err_grps = []
        for i in pot_err:
            pot_err_grps.append(groups[i]) 
        self.outliers_flagged[name] = pot_err_grps

        if(pot_err_grps):
            ax = visualize_outliers(col, ax, pot_err_grps, color='red')
    
    def flag_univariate_outliers(self,col):
        col, name = self.__check_col(col)
        if(not name):
            return
        
        outliers = zscore_method(col)
        if(not outliers.any()):
            print('No outliers found')
            return
        groups = group_outliers(outliers)
        self.outliers[name] = groups

        ax = col.plot()
        ax = visualize_outliers(col, ax, groups, color='green')
        
        means = []
        for i in range(len(groups)):
            subseries = col.iloc[groups[i][0]-1:groups[i][-1]]
            means.append(subseries.mean())
        
        pot_err = zscore_method(means,1)
        pot_err_grps = []
        for i in pot_err:
            pot_err_grps.append(groups[i]) 
        self.outliers_flagged[name] = pot_err_grps

        if(pot_err_grps):
            ax = visualize_outliers(col, ax, pot_err_grps, color='red')

    def clean_flagged_outliers(self, col, mode='auto', manual = []):
        col, name = self.__check_col(col)
        if(not name):
            return
    
        if(mode=='man' and manual and isinstance(manual, list)):
            print('Cleaning the manually flagged outliers: {0}'.format(manual))
            flagged_groups = []
            try:
                groups = self.outliers[name]
            except KeyError:
                print('No outliers known for this column. Consider running {0} first'.format(self.show_multivariate_outliers))
                return
                
            for i in manual:
                flagged_groups.append(group[i])           

        elif(mode=='auto'):
            try:
                flagged_groups = self.outliers_flagged[name]
                print('Cleaning the automatically flagged outliers')
            except KeyError:
                print('Column does not have any outliers atomatically flagged. Consider running {0} first'.format(self.show_multivariate_outliers))
                return
        elif(mode=='all'):
            try:
                flagged_groups = self.outliers[name]
            except KeyError:
                print('No outliers known for this column. Consider running {0} first'.format(self.show_multivariate_outliers))
                return

        print('Cleaning {0} outliers'.format(len(flagged_groups)))
        for i in range(len(flagged_groups)):
            group = flagged_groups[i]
            for n in range(len(group)):
                self.df[name].iloc[group[n]] = float('NaN')
                #print('Changed {0}'.format(group[n]))

        #self.df.fillna(0.2,inplace=True)
        self.interpolate(method='time')

        ax = self.df[name].plot()
        ax = visualize_outliers(self.df[name], ax, self.outliers[name], color='green')
        ax = visualize_outliers(self.df[name], ax, self.outliers_flagged[name], color='green')
    
    def print_cols(self):
        for i in range(len(self.df.columns)):
            print('{0}: {1}'.format(i, self.df.columns[i]))

    def __check_col(self, col):
        if(isinstance(col, str)):
            name = col
            col = self.df[name]
        elif(isinstance(col, pd.core.series.Series)):
            name = col.name
        else:
            print('Column not in dataframe')
            return False, False
        return col, name

    def to_csv(self, location, index=False):
        #2. apply time format to index
        self.df.index = self.df.index.strftime(self.time_format)
        self.df.to_csv(location,index=index)
