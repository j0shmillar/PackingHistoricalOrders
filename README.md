# PackingHistoricalOrders

Python script for simulating packing historical orders.

**Instructions:**

The script can be run from the command line like so:
   
     python sim.py "lockerLayout.json" "orderData.txt"
                  
For example,
  
     python sim.py "truck7.json" "Order_data_aug_sep_oct_HD_Ver2.txt"

Results will be printed to the terminal. 
Two csv files will be created - one containing all 'good' orders e.g. "good_orders_truck7.json", and similarly one containing all "bad".  

See "truck7.json" for an example of how to format the lockerLayout.json if adding a new truck.
A similar format must be followed when adding a new truck to the database (must use cadJosh). 
                    
 

