# Monte Carlo Forcasting

Forked from https://github.com/LetPeopleWork/MonteCarloCSV
Kudos for the initial code goes to (https://www.linkedin.com/in/huserben/).

I forked this repo to add a few features:

1. Added the possibility to use Story points int the forecast. The original code worked only with closed items. 
2. Added the possibility to forcast from a particular date and have titles in graphs configurable
3. Added some strongly typing as this is a requirement for code to be checked in the company i work for. 


## Configuration Options
In `MonteCarlo.py` the following default values are defined:

```
parser.add_argument("--FileName", default='issue_throughput_60d.csv')
parser.add_argument("--History", default="60")
parser.add_argument("--Delimeter", default=";")
parser.add_argument("--ClosedDateColumn", default="Done Date")
parser.add_argument("--DateFormat", default="%Y-%m-%d")
parser.add_argument("--ItemsColumn", default="Points")
parser.add_argument("--StartDate", default = "01.05.2024")
parser.add_argument("--TargetDate", default="01.06.2024")
parser.add_argument("--TargetDateFormat", default="%d.%m.%Y")
parser.add_argument("--RemainingItems", default="500")
parser.add_argument("--SaveCharts", default=True, action=argparse.BooleanOptionalAction)
parser.add_argument("--ItemsName", default = "Points")
```


### Arguments
Name | Description |
--- | --- |
--FileName | The name of the csv file to be used for the simulation. Default is 'issue_throughput_60d.csv'. Can be a relative path (using '.') or an absolute one |
--Delimeter | The delimeter that is used in the file specified. Default is ; |
--ClosedDateColumn | The name of the column in the csv file that contains the closed date. Default is "Closed Date". |
--DateFormat | The format of the date in the csv file. Default is "%Y-%m-%d". Check [Python Dates](https://www.w3schools.com/python/python_datetime.asp) for the options you have (or ask ChatGPT) |
--StartDate | The start date for the simulation. Default is "01.05.2024" |
--TargetDate | The target date for the simulation. Default is "08.04.2024". It might be obvious, but that date should be in the future |
--TargetDateFormat | The format of the target date. Default is "%d.%m.%Y". Check [Python Dates](https://www.w3schools.com/python/python_datetime.asp) for the options you have (or ask ChatGPT) |
--RemainingItems | The number of remaining items for the simulation. Default is 78. |
--SaveCharts | If specified, the charts created during the MC Simulation will be stored in a subfolder called "Charts". |
--ItemsName | The name of the items column in the csv file. Default is "Points" |
