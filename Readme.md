# Extract State Codes Data

This project is part of a workflow to extract a structured data representation of statutes and annotations from the raw .rtf files that make up state code releases.

This project started as a fork of the UniCourt beautiful state codes repo that generates nicer HTML versions of state laws.

Currently this code only supports the statue of Kentucky. Other states that were covered by the UniCourt project are still represented in this codebase, but the files have not been updated.

The parser also only currently supports title rtf files. Files for the constitution, full text ag opinions, new sections, or other non-title rtf files should be removed from the batch of files to be processed.


** Usage

1. Create new folder named **transforms**

2. Based on the state create a folder called *transforms/{state_name}*

3.Inside the above folder based on the release create a folder oc{stateCode}/{release} which will contain raw files (raw files are textutil output files)

4. Example folder structure:

                    ```
                    project
                    │   README.md
                    │   requirements.txt    
                    │
                    └───html_parser
                    │   │   file011.py
                    │   │   file012.py
                    |
                    └───transforms
                    │   └───ky
                    │       └───ocky
                    │              └───raw
                    │                     title_01.html
    

5. Python3.8 should be installed in development environment to run this project  

6. run **pip install -r requirements.txt** to install all the packages required

**Usage:** python html_parser/html_parse_runner.py

        [--state_key (KY)]
        
        [--release_label (Release-75)]
        
        [--release_date (DD-MM-YYYY)]
        
        [--input_file_name (gov.ky.ocga.title.01.html) This is an optional argument,
        
        if this argument is not passed all the files for provided release label will be parsed]
