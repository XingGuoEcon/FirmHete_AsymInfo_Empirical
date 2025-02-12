# A Quick Tour

## Background
We are trying to understand how monetary policy affects the cost of issuing equity. 

* Cost of Issuing Equity

    It is measured by the accumulated abnormal return around the issuance events. Details can be found in Data/Appendix/GOW_DataAppendix.pdf, as well as a series of codes Data/Micro_data/codes/Step_1_1_xxxxx.py~Step_1_3_xxxxxx.py.

* Regression Design

    Essentially, we are estimating how much measured equity issuance costs would vary to the exposure of the issuance event to monetary policy shocks. The detailed design can be found in Section 2.4 of Data/Appendix/GOW_DataAppendix.pdf, as well as a series of codes including Data/Micro_data/codes/Step_4_1_xxxxxxx.py~Step_4_2_xxxxxx.py and Data/Micro_data/codes/Study_3_2_xxxxxxx.py.

## Objective
We want to provide some side evidence to support our interpretation of the equity issuance cost variation through information asymmetry. Specifically, we would like to investigate the variation of cost of equity issuance through two dimensions:

* Variation unconditional on monetary policy shocks

    Regardless of the monetary policy shocks, are the measured equity issuance costs different for the firms which are more subject to information asymmetry issue?

* Variation conditional on monetary policy shocks

    Is there any dependence of the responsiveness of measured equity issuance costs to monetary shocks on the degree of information asymmetry issue?

## Brief Execution Guidance
1. We can start directly from the constructed datasets RegSample.p and Sample_CleanedCS_Q.p in Data\Micro_data\Trial_SideEvidence_InformationAsymmetry.

    * RegSample.p

        This a sample of issuance events and the relevant information (different measured issuance costs, firm characteristics, aggregate economic conditions, different measured exposure to monetary shocks). More information about how this sample is constructed can be found in codes in Data/Micro_data/codes.
    * Sample_CleanedCS_Q.p

        This is a cleaned quarterly Compstat data set. The variables you might need is:
        1. gvkey: firm id, you need to use this to merge the information into regression sample.
        2. Age_Y: measured age, could be useful as a proxy for information asymmetry.
        3. sic (or FF10_Code/FF10_Name): industry code, could be useful as a proxy for information asymmetry.
        4. RDExp: R&D expenditure, useful as a proxy for information asymmetry.

        Other variables are named in very intuitive way and their name should be easily interpretable.
2. We can investigate our targetted questions by flexibly choosing any methods: summary statistics by groups, regression over subsamples, or regression with extra dummies, etc. ...

3. No need to format the code/file too much, just make sure the structure of the code/file is organized and easy to track.

## Regression Design
We can run the regression:

$` CAR_{i,j,t}= \alpha + \beta \cdot v^{ms}_{t} + \gamma \cdot v^{ms}_{t} \cdot I_{i,j,t} + \theta \cdot I_{i,j,t} + \Gamma_{Y}\cdot Y_{t} + \Gamma_{X}\cdot X_{i,j,t} + \varepsilon_{i,j,t} `$

where 

* $` i `$ is the index for issuance event, $` j `$ is the index for firm, and $` t `$ is the index for quarter;
* $` CAR_{i,j,t}`$ is the measured equity issuance cost, i.e. accumulated abnormal return in the issuance event $` i `$;
* $` v^{ms}_{t} `$ is the measured exposure to monetary policy shock of the issuance event $` i `$;
* $` I_{i,j,t} `$ is the proxy for information asymmetry issue;
* $` Y_{t} `$ denotes the controls for macroeconomic condition;
* $` X_{t} `$ denotes the controls for firm characteristics;

The candidate for $` I_{i,j,t} `$ could be:
1. industry of firm $` j `$;
2. ratio between R&D expenditure and the total investment expenditure (capital expenditure + R&D expenditure);
3. quantile category of market to book value ratio of firm $` j `$ in period $` t `$;

 
