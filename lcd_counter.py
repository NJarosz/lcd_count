import time
import csv
from datetime import datetime, date, timedelta
from mfrc522 import SimpleMFRC522
import I2C_LCD_driver
from gpiozero import Button, InputDevice, OutputDevice
import pickle
import mysql.connector
import os

with open("/etc/hostname", "r") as hn:
    pi = hn.readline().rstrip("\n")
    
count_num = int(''.join(i for i in pi if i.isdigit()))
shot_sig = Button(4)
button1 = Button(26)
button2 = Button(12)
sig_out = OutputDevice(17)
reader = SimpleMFRC522()
lcd = I2C_LCD_driver.lcd()
csv_path = "/home/pi/Documents/CSV/"
count_pkl = "/home/pi/Documents/counts.pickle"
prod_vars_pkl = "/home/pi/Documents/vars.pickle"
file_path = ""
logon = "LOG_ON"
logout = "LOG_OFF"
timeout = "TIME_OUT"
mas = "MAS"
mae = "MAE"
shot = "SHOT"
modes = {"setup": 0,
         "standby": 1,
         "menu": 2,
         "run": 3,
         "maint": 4
         }
mode = modes["standby"]
startup = True
maint_msg = "Maintenance"
maint_end_msg = "Maintenance End"
invalid_msg = "Invalid Info"
menu_msg1 = "Setup Mode"
menu_msg2 = "Reset Counter"
count_reset = "Counter= 0"
logoutm = "Logged Out"
timeoutm = "Timed Out"


try:
    db_host = "10.0.0.167"
    db_user = os.environ.get("DB_USER_1")
    db_psw = os.environ.get("DB_PSW_1")
    db_name = "tjtest"
except:
    pass


def read_pckl_counts(pcklfile):
    pickle_in = open(pcklfile, "rb")
    pkl_dict = pickle.load(pickle_in)
    return pkl_dict

def save_vars(dict, pkl_file):
    with open(pkl_file, "wb") as pckl:
        pickle.dump(dict, pckl)

prod_vars_dict = read_pckl_counts(prod_vars_pkl)

def read_machvars_db(count_num=count_num):
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            passwd=db_psw,
            database=db_name
        )
        c = conn.cursor()
        c.execute("SELECT part FROM datavars WHERE counter=%s", (count_num,))
        part = c.fetchone()
        part = str(part[0])

        c.execute("SELECT mach FROM datavars WHERE counter=%s", (count_num,))
        mach = c.fetchone()
        mach = str(mach[0])

        c.execute("SELECT countset FROM datavars WHERE counter = %s", (count_num,))
        countset = c.fetchone()
        countset = int(countset[0])
        c.close()
    except:
        part = str(prod_vars_dict['part'])
        mach = str(prod_vars_dict['mach'])
        countset = int(prod_vars_dict['countset'])

    return part, mach, countset
    
def ret_emp_name(id_num):
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            passwd=db_psw,
            database=db_name
        )
        c = conn.cursor()
        c.execute("SELECT name FROM employees WHERE id=%s", (id_num,))
        emp_name=c.fetchone()
        emp_name=str(emp_name[0])
        c.close()
        return emp_name
    except:
        return None
              

def evaluate(part, mach, countset, dicti):
    b = False
    try:
        if part and len(part) != 0:
            if mach and len(mach) != 0:
                if type(countset) == int:
                    b = True
                    dicti['part'] = part
                    dicti['mach'] = mach
                    dicti['countset'] = countset
    except:
        b = False
    return b, dicti

def update_counts(totalcount, runcount):
    global count_dict
    totalcount +=1
    runcount +=1
    count_dict['totalcount'] = totalcount
    count_dict['runcount'] = runcount
    return totalcount, runcount

def count_reset(runcount):
    global count_dict
    runcount = 0
    count_dict['runcount'] = runcount
    lcd.clear()
    lcd.message("PRESS BUTTON 1",1)
    lcd.message("TO RESET", 2)
    return runcount
                

def invalid_params():
    lcd.clear()
    lcd.message(invalid_msg)
    time.sleep(10)
    lcd.clear()

def create_file_path(day, path=csv_path):
    filename = day.strftime("%Y%m%d") + f"{pi}.csv"
    file_path = path + filename
    return file_path

def create_csv(file):
    """creates a new csv file, inserts a header"""
    with open(file, "a", newline="") as fa, \
            open(file, "r", newline='') as fr:
        writer = csv.writer(fa, delimiter=",")
        line = fr.readline()
        if not line:  # if CSV is empty, add header
            header = ("Type", "pi", "Machine", "Part",
                      "User_ID", "Time", "Date")
            writer.writerow(header)


def add_timestamp(cat, file):
    """opens or creates a csv file with todays date in
    filename. Adds timestamp to that csv including machine
    number, part number, id number, user, time, date"""
    now = time.strftime("%H:%M:%S")
    data = (cat, count_num, mach_num, part_num, emp_num, now, today)
    with open(file, "a", newline="") as fa:
        writer = csv.writer(fa, delimiter=",")
        writer.writerow(data)

def update_csv():
    today = date.today()
    file_path = create_file_path(day=today)
    create_csv(file=file_path)
    return today, file_path


def display_run_info(last_display, last_disp_time):
    lcd.message(run_msg_btm, 2)
    if datetime.now() > last_disp_time + timedelta(seconds=5):
        if last_display != 1:
            lcd.message("                ",1)
            lcd.message(run_msg_top1, 1)
            last_display = 1
        else:
            lcd.message("                ",1)
            lcd.message(run_msg_top2, 1)
            last_display = 0
        last_disp_time = datetime.now()
    return last_display, last_disp_time

def change_msg(msg, sec=1, line=1):
    lcd.clear()
    lcd.message(msg, line)
    time.sleep(sec)

def logout_func(file_path):
    sig_out.off()
    add_timestamp(logout, file_path)
    change_msg(logoutm, sec=1)

try:    
    while True:
        # if mode == modes["setup"]:
        #     change_msg("Setup")
        #     while mode == modes["setup"]:
        #         part_num, mach_num, countset = read_machvars_db()
        #         test, prod_vars_dict = evaluate(part_num, mach_num, countset, prod_vars_dict)
        #         if test is True:
        #             count_dict = read_pckl_counts(count_pkl)
        #             total_count = count_dict['totalcount']
        #             run_count = count_dict['runcount']
        #             if startup is True:
        #                 today, file_path = update_csv()
        #                 mode = modes["standby"]
        #             else:
        #                 time.sleep(.5)
        #                 lcd.message("Press Btn", 2)
        #                 keeplooping = True
        #                 endlooptime = datetime.now() + timedelta(seconds=10)
        #                 while keeplooping == True:
        #                     if button1.is_pressed:
        #                         button1.wait_for_release()
        #                         mode = modes["standby"]
        #                         keeplooping = False
        #                     elif datetime.now() >= endlooptime:
        #                         mode = modes["standby"]
        #                         keeplooping = False
        #
        #         else:
        #             invalid_params()
        #     startup = False
        if mode == modes["standby"]:
            emp_name = None
            emp_num = None
            idn = None
            part_num, mach_num, countset = read_machvars_db()
            test, prod_vars_dict = evaluate(part_num, mach_num, countset, prod_vars_dict)
            if test is True:
                print("TRUE", part_num, mach_num, countset)
                save_vars(prod_vars_dict, prod_vars_pkl)
                count_dict = read_pckl_counts(count_pkl)
                total_count = count_dict['totalcount']
                run_count = count_dict['runcount']
                lcd.clear()
                standby_info_top = f"Part:{part_num}"
                standby_info_btm = f"Cnt:{total_count} Mch:{mach_num}"
                print(standby_info_top)
                lcd.message(standby_info_top, 1)
                lcd.message(standby_info_btm, 2)
                timer_start = datetime.now()
                time.sleep(15)
                if startup is True:
                    today, file_path = update_csv()
                    mode = modes["standby"]
                while mode == modes["standby"]:
                    if datetime.now() >= timer_start + timedelta(seconds=7):
                        part_num, mach_num, countset = read_machvars_db()
                        test, prod_vars_dict = evaluate(part_num, mach_num, countset, prod_vars_dict)
                        save_vars(prod_vars_dict, prod_vars_pkl)
                        timer_start = datetime.now()
                        standby_info_top = f"Part:{part_num}"
                        standby_info_btm = f"Cnt:{total_count} Mch:{mach_num}"
                        lcd.clear()
                        lcd.message(standby_info_top, 1)
                        lcd.message(standby_info_btm, 2)
                    if date.today() != today:
                        today, file_path = update_csv()
                    idn, emp_num = reader.read_no_block()
                    if emp_num != None:
                        emp_num = emp_num.strip()
                        if emp_num == '':
                            pass
                        else:
                            emp_name = ret_emp_name(emp_num)
                            emp_count = 0
                            add_timestamp(logon, file_path)
                            mode = modes["run"]
                    if button2.is_pressed:
                        button2.wait_for_release()
                        time.sleep(0.2)
                        mode = modes["menu"]
            else:
                invalid_params()
            startup = False
        elif mode == modes["menu"]:
            lcd.clear()
            menu = 1
            time.sleep(.5)
            while mode == modes["menu"]:
                if menu == 1:
                    lcd.message(menu_msg1)
                    # if button1.is_pressed:
                    #     button1.wait_for_release()
                    #     mode = modes["setup"]
                    if button2.is_pressed:
                        button2.wait_for_release()
                        menu = 2
                        change_msg(menu_msg2, sec=0)
                if menu == 2:
                    time.sleep(.5)
                    if button1.is_pressed:
                        button1.wait_for_release()
                        total_count = 0
                        change_msg(count_reset, sec=3)
                        mode = modes["standby"]
                    if button2.is_pressed:
                        button2.wait_for_release()
                        time.sleep(0.3)
                        menu = 1
                        lcd.clear()
        elif mode == modes["run"]:
            sig_out.on()
            run_msg_top1 = f"{part_num}  {mach_num}"
            run_msg_top2 = f"{emp_num} {emp_name}"
            last_display = 0
            last_disp_time = datetime.now()
            now = datetime.now()
            lcd.clear()
            lcd.message(run_msg_top2, 1)
            while mode == modes["run"]:
                run_msg_btm = f"Cnt:{emp_count}, {total_count}"
                last_display, last_disp_time = display_run_info(last_display, last_disp_time)
                if run_count == countset:
                    sig_out.off()
                    run_count = count_reset(run_count)
                    button1.wait_for_press()
                    button1.wait_for_release()
                    lcd.clear()
                    lcd.message(run_msg_top2, 1)
                    sig_out.on()
                elif shot_sig.is_pressed:
                    shot_sig.wait_for_release()
                    emp_count += 1
                    total_count, run_count = update_counts(total_count, run_count)
                    save_vars(count_dict, count_pkl)
                    add_timestamp(shot, file_path)
                    now = datetime.now()
                    time.sleep(0.1)
                elif datetime.now() >= now + timedelta(seconds=300):
                    add_timestamp(timeout, file_path)
                    sig_out.off()
                    change_msg(timeoutm, sec=5)
                    mode = modes["standby"]
                if button1.is_pressed:
                    button1.wait_for_release()
                    logout_func(file_path)
                    mode = modes["standby"]
                if button2.is_pressed:
                    button2.wait_for_release()
                    sig_out.off()
                    mode = modes["maint"]
        elif mode == modes["maint"]:
            add_timestamp(mas, file_path)
            change_msg(maint_msg)
            while mode == modes["maint"]:
                if button1.is_pressed:
                    button1.wait_for_release()
                    add_timestamp(mae, file_path)
                    logout_func(file_path)
                    mode = modes["standby"]
                if button2.is_pressed:
                    button2.wait_for_release()
                    add_timestamp(mae, file_path)
                    change_msg(maint_end_msg, sec=1)
                    mode = modes["run"]
except KeyboardInterrupt:
    lcd.clear()
except Exception as e:
    lcd.clear()
    lcd.message("ERROR")
    print(e)
