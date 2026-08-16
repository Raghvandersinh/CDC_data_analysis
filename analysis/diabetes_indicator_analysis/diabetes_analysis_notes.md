# What is this data?

## Before we start analyzing, lets understand the data first:

- This data is provided by the CDC(Centers for Disease Control and Prevention) and is specifically using the USDSS (United States Diabetes Surveillance System). As the name suggests it tracks people with diabetes based on Age, Race, Sex, Education, Population, and Other Stratification.

- We are currently using the USDSS National Other Diabetes Indicators, which does not include location but rather includes Other Stratification 

- This data survillance mostly consists of type 2 diabetes, 90%-95% of accounted diabetes are diagnosed are type 2 rest 10%-5% are type 1 diabetes. 

## What are the columns we are working with?

|Columns|Type|Description|
|-------|----|-----------|
|Year|Text| Year that the data represents|
|Indicator|Text|Specific health measures being reported. This is the key detail|
|Unit|Text|How the estimates is presented|
|Estimates|Float|The calculated value of the indicator|
|SE Estimates|Float| Standard Error for Estimate Lower the Number the more precise the Estimate|
|Lower limit|Float| The Lower bound of the 95% Confidence interval|
|Upper limit|Float|The Upper bound of the 95% Confidence interval|
|Population|Text| The Broad group being measured|
|Age|Text|The Age group for this specific estimate|
|Race|Text|The Race for this specfic estimate|
|Sex|Text|The sex for this specfic estimate|
|Eductaion|Text|The education level for this specfic estimates|
|Other Stratification|Text|The Other Stratification level for this specific estimates|

## Data Exploration and Quality Check