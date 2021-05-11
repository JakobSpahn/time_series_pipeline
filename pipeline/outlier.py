from math import isnan

import pandas as pd
import scipy as sp
import numpy as np
from sklearn.covariance import MinCovDet
from scipy.stats import chi2

def high_correlators(df, score):
    matrix = df.corr()
    cols = df.columns

    corrs ={}

    for i in range(len(cols)):
        column = matrix[cols[i]]
        name = column.name
        good = []
        for n in range(len(column)):
            isna = isnan(column[n])
            if(name!=column.index[n] and not isna):
                if(column[n]>=score):
                    good.append(column.index[n])
        if(good):
            corrs[name] = good
        
    return corrs

def mahalanobis_method(df):
    #M-Distance
    x_minus_mu = df - np.mean(df)
    cov = np.cov(df.values.T)                           #Covariance
    inv_covmat = sp.linalg.inv(cov)                     #Inverse covariance
    left_term = np.dot(x_minus_mu, inv_covmat) 
    mahal = np.dot(left_term, x_minus_mu.T)
    md = np.sqrt(mahal.diagonal())
    
    #Flag as outlier
    outlier = []
    #Cut-off point
    C = np.sqrt(chi2.ppf((1-0.001), df=df.shape[1]))    #degrees of freedom = number of variables
    for index, value in enumerate(md):
        if value > C:
            outlier.append(index)
        else:
            continue
    return outlier, md

def robust_mahalanobis_method(df):
    #Minimum covariance determinant
    rng = np.random.RandomState(0)
    real_cov = np.cov(df.values.T)
    X = rng.multivariate_normal(mean=np.mean(df, axis=0), cov=real_cov, size=506)
    cov = MinCovDet(random_state=0).fit(X)
    mcd = cov.covariance_ #robust covariance metric
    robust_mean = cov.location_  #robust mean
    inv_covmat = sp.linalg.inv(mcd) #inverse covariance metric
    
    #Robust M-Distance
    x_minus_mu = df - robust_mean
    left_term = np.dot(x_minus_mu, inv_covmat)
    mahal = np.dot(left_term, x_minus_mu.T)
    md = np.sqrt(mahal.diagonal())
    
    #Flag as outlier
    outlier = []
    C = np.sqrt(chi2.ppf((1-0.001), df=df.shape[1]))#degrees of freedom = number of variables
    for index, value in enumerate(md):
        if value > C:
            outlier.append(index)
        else:
            continue
    return outlier, md

def zscore_method(col, threshold=3):
    z = np.abs(sp.stats.zscore(col))
    out = np.where(z>threshold)
    
    return out[0] #np.where returns tuple containing array 

def group_outliers(out):
    cons = []
    comp = out[0]
    curr = []
    for i in range(len(out)):
        if(out[i] >= comp and out[i] <= comp+4):
            curr.append(out[i])
            comp = out[i]+1
        else:
            cons.append(curr)
            curr = [out[i]]
            comp = out[i]+1
            
    if(curr):
        cons.append(curr)

    return cons

def extend_outliers(groups, threshold=3):
    for i in range(len(groups)):
        group = groups[i]
        #print(group)
        for n in range(threshold):
            if(group[0]>1):
                group.insert(0,group[0]-1)
                group.append(group[-1]+1)
        groups[i] = group
        #print(group)
    return groups

def visualize_outliers(col, ax, out_groups, color='red'):
    for i in range(len(out_groups)):
            col.iloc[out_groups[i][0]-1:out_groups[i][-1]].plot(ax=ax, color=color)
    return ax
