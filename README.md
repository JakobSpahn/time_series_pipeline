# time_series_pipeline
Framework for pre-processing time series data. Ideal for usage in Ipython-notebooks.  
Source-Code for the KEEN Hackathon Challenge: 'AI-Based Automation of Industrial Data Pre-Processing' 
 
## Installation  
- Run: ```python setup.py develop```  

## Usage and [Examples](/examples):
For each of the two cleaned examples, there are Ipython-notebooks detailing the steps that have been run through to process the examples.  
Each data processing step is detailed in these notebooks.  
- example_1.csv: this example stems from /data/real/00-complete/dirty_data.csv
- example_2.csv: this example stems from /data/real/01-dirty-baseline/data-000.csv 

## Strategies
### Filling of Missing Values
Missing values such as NaNs, connectivity/measurement errors, or empty samples (due to resampling) will be filled using interpolation.  
If gaps of missing values exceed a pre-defined limit, they will be skipped.

### Outlier Detection
- This is one of the most sensitive parts of pre-processing. Some outliers may be measurement errors, while others may be natural anomalies.  


Thus, our solution is semi-automatic: outliers that may be measurement errors (or NaN-values e.g. '9999') are only flagged. 
The user then decides whether the flagged outliers should be cleaned.  
Following this, the user will have to look at each column individually.  

Outliers are detected depending on the column:  
If a column has high correlation (>0.7) with other columns, it will use multivariate outlier detection using those other columns.  
For this, the mahalanobis-distance is computed for each of the data points.  

If 

## Issues and Limitations
### Issues with datasets from the /data/example/ category:
- conv_unit:		      processing but ignores units
- formats: 		        can only process matrix-format (not list)
- lagging: 		        can process without error, but cannot infer lagging value from second column
- partial_noise: 	    succesfully processes but does not reduce any noise
- single_timeshifts:	pipeline can't handle multiple files. They would have to be processed sequentially
### Other issues:
- framework only accepts ```.csv``` data

