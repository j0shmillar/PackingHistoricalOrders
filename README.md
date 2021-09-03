# PackingHistoricalOrders

Python script for simulating packing historical orders.

**Instructions:**

The script can be run from the command line like so:
   
     python sim.py "lockerLayout.json" "orderData.txt"
                  
For example,
  
     python sim.py "truck7.json" "Order_data_aug_sep_oct_HD_Ver2.txt"

Results will be printed to the terminal. 
Two csv files will be created - one containing all 'good' orders (e.g. "good_orders_truck6.json"), and similarly one containing all "bad".  

If adding a new truck, see "truck6.json" and "truck7.json" for examples of how to format the locker layout. 
A similar format must be followed when adding a new truck to the database (i.e. cadJosh). 
                    
 

