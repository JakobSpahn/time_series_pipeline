import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 
from dateutil import parser

from .utils import get_header

from datetime import datetime, timedelta

class Dataset:
    def __init__(self, location):

        header, unit = get_header(location) #Get row number of header. If detected, also row number of unit row
        self.df = pd.read_csv(location, header=header) #This needs to be smarter (header=2 is not general enough)

        self.units = None
        self.time_format = None
        self.sampling_rate = None
        self.average = None
        self.std_dev = None

        if(unit):
            self.units = self.df.iloc[0].values
            self.df = self.df.iloc[1:]

    def infer_format(self): #ToDo: Functionality to differentiate between US and EU format.
        #Get first and last (correct) timestamp
        first_stamp = parser.parse(self.df.iloc[0,0])
        last_stamp = parser.parse(self.df.iloc[-1,0])

        diff = last_stamp - first_stamp

        base_format = '%H:%M:%S'
        time_format = base_format

        if(diff.days >= 1):
            time_format =  '%Y-%m-%D ' + base_format

        self.time_format = time_format
        return time_format

    def apply_format(self):
        next_idx = 0
        group = 0
        
        #Can we speed this up? --> use numpy vectorization
        for i in range(len(self.df)):
            val = self.df.iloc[i,0]
            
            try:
                val = parser.parse(val)
                val = val.strftime(self.time_format)
                next_idx += 1

            #except TypeError as e:
                #If its already NaT
                
            except ValueError:
                if next_idx == i:
                    next_idx = i+1
                else:
                    group = group + 1
                
                #print("Wrong val: {0}; Replaced with {1}".format(val, hex(group)))
                val = hex(group)
                
            self.df.iloc[i,0] = val
            
        #return self.df

    def clean_stamps(self):
        
        #Drop Duplicates first
        self.df = self.df.drop_duplicates()
        self.df.reset_index(drop=True, inplace=True)
        
        #Name of first column (supposed to be time column)
        self.name_time = self.df.columns[0]
        
        #Get List of all duplicated indices
        df_i_dup = self.df[self.df.duplicated(subset=[self.name_time],keep=False)]
        unique_dup = df_i_dup[self.name_time].unique() #[11:01:00, 0x0, 0x1]
        print(unique_dup)

        for idx,i in enumerate(unique_dup):
            print('Changing duplicate timestamp {0}'.format(i))
            
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
            self.df[self.name_time] = pd.to_datetime(self.df[self.name_time])
            self.df = self.df.set_index(self.name_time)
            return True
        else:
            print('Index already datetime')
            return True
        
        return False #Maybe not needed

    def median_sampling_rate(self):
        median = None
        if(self.time_as_index()):
            values = self.df.index.to_series().diff()
            print(values.value_counts())
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
        
    
    def interpolate(self):
        #Add limit
        self.df = self.df.interpolate(method='time').ffill().bfill()
        na_rows = len(self.df[self.df.isnull().any(axis=1)])
        print('After interpolation {0} rows contain nan values'.format(na_rows))


    def to_csv(self, location, index=False):
        self.df.to_csv(location,index=index)