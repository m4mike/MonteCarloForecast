import os
import random
from datetime import date, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Tuple, Dict, Optional

class MonteCarloService:
    
    def __init__(self, history_in_days: int, save_charts: bool = False, trials: int = 100000) -> None:
        self.trials: int = trials        
        self.history_in_days: int = history_in_days
        
        self.percentile_50: float = 0.5
        self.percentile_70: float = 0.7
        self.percentile_85: float = 0.85
        self.percentile_95: float = 0.95

        script_path: str = os.path.dirname(os.path.abspath(__file__))
        self.charts_folder: str = os.path.join(script_path, 'Charts')
        self.save_charts: bool = save_charts

        if save_charts and not os.path.exists(self.charts_folder):
            os.makedirs(self.charts_folder)
        
    def create_closed_items_history(self, items: List) -> Dict:
        print(f"Getting items that were done in the last {self.history_in_days} days...")       
        time_delta: date = date.today() - timedelta(self.history_in_days)
        df: pd.DataFrame = pd.DataFrame.from_records([item.to_dict() for item in items])        
        
        closed_items: pd.DataFrame = pd.DataFrame()
        closed_items = pd.concat([closed_items, df[df.closed_date >= time_delta]])
        
        closed_items_hist: Dict = {}
        
        if self.save_charts:
            tp_run_chart_path: str = os.path.join(self.charts_folder, 'Throughput_Run_Chart.png')
            print(f"Storing Chart at {tp_run_chart_path}")
            plt.bar(list(closed_items_hist.keys()), closed_items_hist.values(), color='b')
            plt.savefig(tp_run_chart_path)
        
        print(f"Found {len(closed_items)} items that were closed in the last {self.history_in_days} days")
                    
        return closed_items_hist
    
    def how_many(self, start_date: date, target_date: date, closed_items_history: Dict, title: str = "How Many {item_type} will be done till {target_date}") -> Tuple:
        monte_carlo_simulation_results: Dict = self.__run_monte_carlo_how_many(start_date, target_date, closed_items_history)
        
        return self.__get_predictions_howmany(monte_carlo_simulation_results, title)
        
    def when(self, remaining_items: int, closed_items_history: Dict, start_date: date, target_date: Optional[date] = None, title: str = "When will {items_name} be done ?") -> Tuple:
        monte_carlo_simulation_results: Dict = self.__run_monte_carlo_when(start_date, remaining_items, closed_items_history)
        
        days_to_target_date: Optional[int] = (target_date - date.today()).days if target_date else None
        
        return self.__get_predictions_when(monte_carlo_simulation_results, start_date, days_to_target_date, title)

    def __run_monte_carlo_when(self, start_date: date, remaining_items: int, closed_items_history: Dict) -> Dict:        
        time_delta: date = start_date - timedelta(self.history_in_days)
        monte_carlo_data: List[int] = self.__prepare_monte_carlo_dataset(start_date, time_delta, closed_items_history)            
                
        mc_results: Dict[int, int] = {}
                
        for i in range(self.trials):
            day_count: int = 0
            finished_item_count: int = 0
                    
            while finished_item_count < remaining_items:
                day_count += 1
                rand: int = random.randint(0, len(monte_carlo_data) - 1)
                finished_item_count += monte_carlo_data[rand]
                        
            if day_count in mc_results:
                mc_results[day_count] += 1
            else:
                mc_results[day_count] = 1
                
        return mc_results

    def __get_predictions_when(self, mc_results: Dict, start_date: date, days_to_target_date: Optional[int] = None, title: str = "") -> Tuple:        
        sorted_dict: Dict = {k: v for k, v in sorted(mc_results.items())}
                
        percentile_50_target: int = self.trials * 0.5
        percentile_70_target: int = self.trials * 0.7
        percentile_85_target: int = self.trials * 0.85
        percentile_95_target: int = self.trials * 0.95

        percentile_50: int = 0
        percentile_70: int = 0
        percentile_85: int = 0
        percentile_95: int = 0
        
        trials_in_time: int = self.trials if days_to_target_date else -1
        
        count: int = 0
                    
        for key, value in sorted_dict.items():
            count += value
                    
            if percentile_50 == 0 and count >= percentile_50_target:
                percentile_50 = key
            elif percentile_70 == 0 and count >= percentile_70_target:
                percentile_70 = key
            elif percentile_85 == 0 and count >= percentile_85_target:
                percentile_85 = key
            elif percentile_95 == 0 and count >= percentile_95_target:
                percentile_95 = key
                
            if trials_in_time == self.trials and key >= days_to_target_date:
                trials_in_time = count
                
        predicted_date_50: date = start_date + timedelta(percentile_50)
        predicted_date_70: date = start_date + timedelta(percentile_70)
        predicted_date_85: date = start_date + timedelta(percentile_85)
        predicted_date_95: date = start_date + timedelta(percentile_95)    
        
        prediction_targetdate: float = 0
        if days_to_target_date:
            prediction_targetdate = (100 / self.trials) * trials_in_time
        
        if self.save_charts:
            vertical_lines_data: List[Tuple[int, str, str, date]] = [
                (percentile_50, '50th Percentile', "red", predicted_date_50),
                (percentile_70, '70th Percentile', "orange", predicted_date_70),
                (percentile_85, '85th Percentile', "lightgreen", predicted_date_85),
                (percentile_95, '95th Percentile', "darkgreen", predicted_date_95)
            ] 
            
            plt.figure(figsize=(15, 9))
            when_chart_path: str = os.path.join(self.charts_folder, 'MC_When.png')
            print(f"Storing Chart at {when_chart_path}")
            plt.bar(list(sorted_dict.keys()), sorted_dict.values(), color='g')

            for position, line_name, color, ddate in vertical_lines_data:
                plt.axvline(x=position, color=color, linestyle='--', label=f"{line_name} ({position} days) -> {ddate}")

            plt.legend()
            plt.title(title)

            plt.savefig(when_chart_path)
            plt.show()

        return (predicted_date_50, predicted_date_70, predicted_date_85, predicted_date_95, prediction_targetdate)

    def __run_monte_carlo_how_many(self, start_date: date, prediction_date: date, closed_items_hist: Dict) -> Dict:
        time_delta: date = start_date - timedelta(self.history_in_days)
        monte_carlo_data: List[int] = self.__prepare_monte_carlo_dataset(start_date, time_delta, closed_items_hist)            
                
        mc_results: Dict[int, int] = {}
        amount_of_days: int = (prediction_date - start_date).days
                
        for i in range(self.trials):
            day_count: int = 0
            finished_item_count: int = 0
                    
            while day_count < amount_of_days:
                day_count += 1
                rand: int = random.randint(0, len(monte_carlo_data) - 1)
                finished_item_count += monte_carlo_data[rand]
                        
            if finished_item_count in mc_results:
                mc_results[finished_item_count] += 1
            else:
                mc_results[finished_item_count] = 1
                
        return mc_results

    def __get_predictions_howmany(self, mc_results: Dict, title: str = "") -> Tuple:        
        sorted_dict: Dict = {k: v for k, v in sorted(mc_results.items(), reverse=True)}
                
        percentile_50_target: int = self.trials * self.percentile_50
        percentile_70_target: int = self.trials * self.percentile_70
        percentile_85_target: int = self.trials * self.percentile_85
        percentile_95_target: int = self.trials * self.percentile_95
        
        percentile_50: int = 0
        percentile_70: int = 0
        percentile_85: int = 0
        percentile_95: int = 0
        
        count: int = 0
                
        for key, value in sorted_dict.items():
            count += value
                    
            if percentile_50 == 0 and count >= percentile_50_target:
                percentile_50 = key
            elif percentile_70 == 0 and count >= percentile_70_target:
                percentile_70 = key
            elif percentile_85 == 0 and count >= percentile_85_target:
                percentile_85 = key
            elif percentile_95 == 0 and count >= percentile_95_target:
                percentile_95 = key
                
        if self.save_charts:
            vertical_lines_data: List[Tuple[int, str, str]] = [
                (percentile_50, '50th Percentile', "red"), 
                (percentile_70, '70th Percentile', "orange"), 
                (percentile_85, '85th Percentile', "lightgreen"), 
                (percentile_95, '95th Percentile', "darkgreen")
            ] 

            plt.figure(figsize=(15, 9))
            how_many_chart_path: str = os.path.join(self.charts_folder, 'MC_HowMany.png')
            print(f"Storing Chart at {how_many_chart_path}")
            plt.bar(list(sorted_dict.keys()), sorted_dict.values(), color='g')
            
            for position, line_name, color in vertical_lines_data:
                plt.axvline(x=position, color=color, linestyle='--', label=f"{line_name} ({position})")

            plt.legend()
            plt.title(title)
            plt.savefig(how_many_chart_path)
            plt.show()
        
        return (percentile_50, percentile_70, percentile_85, percentile_95)

    def __prepare_monte_carlo_dataset(self, start_date: date, time_delta: date, closed_items_hist: Dict) -> List[int]:
        monte_carlo_data: List[int] = []
        
        for i in range((start_date - time_delta).days):
            day: date = date.today() - timedelta(days=i)
            daystr: str = day.strftime("%Y-%m-%d")
            monte_carlo_data.append(closed_items_hist.loc[closed_items_hist['Done Date'] == daystr, 'Items'].sum())
        
        return monte_carlo_data
