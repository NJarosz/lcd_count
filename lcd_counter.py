import time
from datetime import datetime, date, timedelta
from mfrc522 import SimpleMFRC522
import I2C_LCD_driver
from gpiozero import Button, InputDevice, OutputDevice
import mysql.connector

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
file_path = ""
logon = "LOG_ON"
logout = "LOG_OFF"
timeout = "TIME_OUT"
mas = "MAS"
mae = "MAE"
shot = "SHOT"
modes = {0: "setup",
        1: "standby",
        2: "menu1",
        3: "run",
        4: "maint"
         }
mode = modes[0]
startup = True
count_path = "/home/pi/Documents/totalcount"
maint_msg = "Maintenance"
maint_end_msg = "Maintenance End"
invalid_msg = "Invalid Info"
menu_msg1 = "Setup Mode"
menu_msg2 = "Reset Counter"
count_reset = "Counter= 0"
logoutm = "Logged Out"
conn = mysql.connector.connect(
                                host="10.0.0.167",
                                user="python-user",
                                passwd="blue.marker48",
                                database="tjtest"
                            )

def read_machvars_db():
    c = conn.cursor()
    c.execute("SELECT mach FROM datavars WHERE counter=%s", (count_num,))
    mach = c.fetchone()
    mach = int(mach[0])
    c.execute("SELECT part FROM datavars WHERE counter=%s", (count_num,))
    part = c.fetchone()
    part = str(part[0])
    c.close()
    return part, mach
    
def ret_emp_name(id_num):
    c = conn.cursor()
    c.execute("SELECT name FROM employees WHERE id=%s", (id_num,))
    emp_name=c.fetchone()
    emp_name=str(emp_name[0])
    c.close()
    return emp_name
              

def evaluate(part, mach):
    b = False
    try:
        if part and len(part) != 0:
            if type(mach) == int:
                b = True
    except:
        b = False
    return b

def read_count(file=count_path):
    with open(file, "r", newline="") as f:
        total_count = f.readline()
        if len(str(total_count)) == 0:
            total_count = 0
        else:
            total_count = int(total_count)
    return total_count


def write_count(count, file=count_path):
    if count > 999999:
        count = 0
    with open(file, "w") as f:
        f.write(str(count))
                

def invalid_params():
    lcd.clear()
    lcd.message(invalid_msg)
    time.sleep(10)
    lcd.clear()


def add_timestamp(cat):
    """opens or creates a csv file with todays date in
    filename. Adds timestamp to that csv including machine
    number, part number, id number, user, time, date"""
    c = conn.cursor()
    c.execute("INSERT INTO prod_data (Type, pi, Machine, Part, Employee) VALUES (%s,%s,%s,%s,%s)", 
              (cat, pi, mach_num, part_num, empnum))
    conn.commit()
    c.close()
        
        
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

def logout():
    sig_out.off()
    add_timestamp(logout)
    change_msg(lougoutm, sec=1)

try:    
    while True:
        if mode == "setup":
            change_msg("Setup")
            while mode == modes[0]:
                part_num, mach_num = read_machvars_db()
                test = evaluate(part_num, mach_num)
                if test is True:
                    total_count = read_count()
                    if startup is True:
                        mode = modes[1]
                    else:
                        time.sleep(.5)
                        lcd.message("Press Btn", 2)
                        keeplooping = True
                        endtlooptime = datetime.now() + timedelta(seconds=10)
                        while keeplooping == True and datetime.now() <= endtlooptime:
                            if button1.is_pressed:
                                button1.wait_for_release()
                                mode = modes[1]
                                keeplooping = False

                else:
                    invalid_params()
            startup = False
        elif mode == "standby":
            empname = None
            empnum = None
            idn = None
            lcd.clear()
            standby_info_top = f"Part:{part_num}"
            standby_info_btm = f"Cnt:{total_count} Mch:{mach_num}"
            lcd.message(standby_info_top, 1)
            lcd.message(standby_info_btm, 2)
            while True:
                idn, empnum = reader.read_no_block()
                try:
                    empnum = empnum.strip()
                    if empnum == '':
                        empnum = None
                    elif empnum != None:
                        try:
                            empname = ret_emp_name(empnum)
                        except:
                            pass
                        empcount = 0
                        add_timestamp(logon, file_path)
                        mode = modes[3]
                        break
                except:
                    pass
                if button2.is_pressed:
                    button2.wait_for_release()
                    time.sleep(0.2)
                    mode = modes[2]
                    break
        elif mode == "menu1":
            lcd.clear()
            menu = 1
            time.sleep(.5)
            while True:
                if menu == 1:
                    lcd.message(menu_msg1)
                    if button1.is_pressed:
                        button1.wait_for_release()
                        mode = modes[0]
                        break
                    if button2.is_pressed:
                        button2.wait_for_release()
                        menu = 2
                        change_msg(menu_msg2, sec=0)
                if menu == 2:
                    time.sleep(.5)
                    if button1.is_pressed:
                        button1.wait_for_release()
                        total_count = 0
                        write_count(total_count)
                        change_msg(count_reset, sec=3)
                        mode = modes[1]
                        break
                    if button2.is_pressed:
                        button2.wait_for_release()
                        time.sleep(0.3)
                        menu = 1
                        lcd.clear()
        elif mode == "run":
            sig_out.on()
            run_msg_top1 = f"{part_num}  {mach_num}"
            run_msg_top2 = f"{empnum} {empname}"
            last_display = 0
            last_disp_time = datetime.now()
            now = datetime.now()
            lcd.clear()
            lcd.message(run_msg_top2, 1)
            while mode == "run":
                run_msg_btm = f"Cnt:{empcount}, {total_count}"
                last_display, last_disp_time = display_run_info(last_display, last_disp_time)
                if shot_sig.is_pressed:
                    shot_sig.wait_for_release()
                    empcount +=1
                    total_count +=1
                    write_count(count=total_count)
                    add_timestamp(shot)
                    now = datetime.now()
                    time.sleep(0.1)
                elif datetime.now() >= now + timedelta(seconds=300):
                    add_timestamp(timeout)
                    sig_out.off()
                    change_msg(lougoutm, sec=1)
                    mode = modes[1]                   
                if button1.is_pressed:
                    button1.wait_for_release()
                    logout()
                    mode = modes[1]
                if button2.is_pressed:
                    button2.wait_for_release()
                    sig_out.off()
                    mode = modes[4]
        elif mode == "maint":
            add_timestamp(mas)
            change_msg(maint_msg)
            while mode == "maint":
                if button1.is_pressed:
                    button1.wait_for_release()
                    add_timestamp(mae)
                    logout()
                    mode = modes[1]
                if button2.is_pressed:
                    button2.wait_for_release()
                    add_timestamp(mae)
                    change_msg(maint_end_msg, sec=1)
                    mode = modes[3]
except KeyboardInterrupt:
    lcd.clear()
except Exception as e:
    lcd.clear()
    lcd.message("ERROR")
