import argparse
import datetime

from MonteCarloService import MonteCarloService
import pandas as pd

parser = argparse.ArgumentParser()
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

args = parser.parse_args()

file_name = args.FileName
delimeter = args.Delimeter
closed_date_column = args.ClosedDateColumn
date_format = args.DateFormat
items_column = args.ItemsColumn
start_date = datetime.datetime.strptime(args.StartDate, args.TargetDateFormat).date()
history = int(args.History)
remaining_items = int(args.RemainingItems)
target_date = datetime.datetime.strptime(args.TargetDate, args.TargetDateFormat).date()
items_name = args.ItemsName

monte_carlo_service = MonteCarloService(history, args.SaveCharts)

def get_closed_items_history():    
    #work_items = csv_service.get_closed_items(file_name, delimeter, closed_date_column, date_format,items_column=items_column)
    work_items =  pd.read_csv(file_name, sep=delimeter)
    closed_items_history = work_items[[closed_date_column,items_column]]
    closed_items_history=closed_items_history.rename(columns={items_column: 'Items'})
    return closed_items_history

print("================================================================")
print("Starting Monte Carlo Simulation...")
print("================================================================")  
print("Parameters:")
print(f"FileName: {args.FileName}")
#print(f"Delimeter: {args.Delimeter}")
#print(f"ClosedDateColumn: {args.ClosedDateColumn}")
#print(f"Items cloumn: {args.ItemsColumn}")
print(f"History: {args.History}")
print(f"StartDate: {args.StartDate}")
print(f"TargetDate: {args.TargetDate}")
print(f"RemainingItems: {args.RemainingItems}")
print("----------------------------------------------------------------")
   
closed_items_history = get_closed_items_history()        
if len(closed_items_history) < 1:
    print("No closed items - skipping prediction")
    exit()

print(f"Running simulation on how many points can be done between {start_date} and {target_date}...")
## Run How Many Predictions via Monte Carlo Simulation for our specified target date
predictions_howmany_50 = predictions_howmany_70 = predictions_howmany_85 = predictions_howmany_95 = 0
if target_date:
    (predictions_howmany_50, predictions_howmany_70, predictions_howmany_85, predictions_howmany_95) = \
        monte_carlo_service.how_many(start_date,target_date, closed_items_history,f"How Many {items_name} will be done between {start_date} and {target_date} based on last {history} days performance")
           

print(f"Running simulation on when {remaining_items} {items_name} will be done.")
## Run When Predictions via Monte Carlo Simulation - only possible if we have specified how many items are remaining
predictions_when_50 = predictions_when_70 = predictions_when_85 = predictions_when_95 = datetime.date.today()
predictions_targetdate_likelyhood = None

if remaining_items > 0:
    (predictions_when_50, predictions_when_70, predictions_when_85, predictions_when_95, predictions_targetdate_likelyhood) = \
        monte_carlo_service.when(remaining_items, closed_items_history, start_date,target_date,f"When will {remaining_items} {items_name} be done based on last {history} days performance")

    
print("================================================================")
print("Summary")
print("================================================================")

print(f"How many {items_name} will be between {start_date} and {target_date}:")
print("50%: {0}".format(predictions_howmany_50))
print("70%: {0}".format(predictions_howmany_70))
print("85%: {0}".format(predictions_howmany_85))
print("95%: {0}".format(predictions_howmany_95))
print("----------------------------------------")

if remaining_items != 0:
    print(f"When will {remaining_items} {items_name} be done:")
    print(f"50%: {predictions_when_50}")
    print(f"70%: {predictions_when_70}")
    print(f"85%: {predictions_when_85}")
    print(f"95%: {predictions_when_95}")
    print("----------------------------------------")
    print(f"Chance of finishing the {remaining_items} remaining {items_name } till {target_date}: {predictions_targetdate_likelyhood}%")