# time_series_pipeline
KEEN Challenge Source Code for Time Series Data Pipeline
## Framework for pre-processing data. Ideal for jupyter notebook
## Installation  
Run: ```python setup.py develop```  

## Pfad zu den Examples, Erklären, dass die notebooks die lösung enthalten
## Vorgehen outlier detection. Nach welchen Regeln funktioniert flagging?


## Welche Besipiele haben funktioniert und welche nicht?
--> conv_unit:		processing but ignores units
--> formats: 		can only process matrix-format (not list)
--> lagging: 		can process without error, but cannot infer lagging value from second column
--> na_base: 		succesfully processes and replaces nan 
--> na_flag: 		succesfully processes and replaces nan
--> na_replacement: 	succesfully processes using outlier detection (semi-automatic, requires user input)
--> partial_noise: 	succesfully processes but does not reduce any noise
--> single_timeshifts:	pipeline can't handle multiple files. They would have to be processed sequentially

## Andere Limitations?
