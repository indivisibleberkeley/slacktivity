#!/usr/bin/env python3

import os
import numpy as np
import json
import datetime
from scipy import optimize
from matplotlib import pyplot as plt
import subprocess

XMAX = 175
YMAX = 1500

def getlogs(enddate):
    activelog = []
    users = {}
    cwd = os.getcwd()
    
    with open("users.json") as f:
        data = json.load(f)
        for user in data:
            users[user['name']] = "{}".format(user['id'])
    for user in users:
        activity = 0
        for item in os.walk(cwd):
            curdir = item[0]
            if curdir is not cwd:
                files = item[2]
                for f in files:
                    if ".json" in f:
                        thisdate = datetime.datetime.strptime(f.strip(".json"),"%Y-%m-%d").date()
                        if thisdate < enddate:
                            fpath = os.path.join(curdir,f)
                            with open(fpath) as log:
                                contents = log.read()
                                activity += contents.count("\"user\": \"{}\"".format(users[user]))
        if activity > 0:
            activelog.append((user,activity))

    a = np.array(activelog,dtype=([('name',np.str_,50),('activity',np.int)]))
    a.sort(axis=0,order='activity')
    y = np.flipud(a)
    np.savetxt('active.log',y,delimiter=',',fmt="%s")
    x = np.linspace(1,len(y),len(y))
    return x,y

def plot_stuff(x,y,y2,fname,title,plottext,annotate=False):
    if y.size == 0:
        print("Nothing to print for {}!".format(fname))
        return
    x2 = range(0,XMAX,1)
    amp,index = get_power(x,y['activity'])
    
    fig1 = plt.figure()
    ax1 = fig1.add_subplot('211')
    ax1.plot(x, y['activity'],linestyle='none',marker='.')
    ax1.plot(y2['num'], y2['activity'], linestyle='none',marker='.')
    if annotate:
        for xy in y2:
            ax1.annotate("{:0.2}".format(xy[1]), xy=(xy[0],xy[2]), xycoords='data', 
                         xytext=(xy[0]-1,xy[2]+50), 
                         textcoords='data', fontsize=5)
                         #arrowprops=dict(facecolor='black', width=0.1, headwidth=2, headlength=5, shrink=0.05),)
    ax1.plot(x2, powerlaw(x2, amp, index), linestyle='--')
    ax1.set_ylabel("posts")
    ax1.grid()
    ax1.set_title(title)
    ax1.set_ylim(0,YMAX)
    ax1.set_xlim(0,XMAX)

    ax2 = fig1.add_subplot('212')
    ax2.loglog(x, y['activity'],linestyle='none',marker='.')
    ax2.plot(y2['num'], y2['activity'], linestyle='none',marker='.')
    if annotate:
        for xy in y2:
            ax2.annotate("{:.2}".format(xy[1]), xy=(xy[0],xy[2]), xycoords='data', 
                         xytext=(xy[0] + 0.0 * np.power(10,0.1*xy[0]),
                                 xy[2] + 5.0 * np.power(10,0.0015*xy[2])), 
                         textcoords='data', fontsize=7)
                         #arrowprops=dict(facecolor='black', width=0.1, headwidth=2, headlength=5, shrink=0.05),)
    ax2.loglog(x2, powerlaw(x2, amp, index), linestyle='--')
    ax2.set_ylabel("posts")
    ax2.grid()
    ax2.set_ylim(1,YMAX*2)
    ax2.set_xlim(0,XMAX)
    ax2.text(1.5, 0.1, "Power Index: {:.2f}".format(-index),fontsize=7, style='italic')
    ax2.text(16, 0.1, "{}".format(plottext),fontsize=7, style='italic')
    
    fig1.savefig("{}.png".format(fname),dpi=300)
    print("saved {}.png".format(fname))
    plt.close(fig1)

def powerlaw(x,amp,index):
    # Define function for calculating a power law
    return amp * (x**index)
    
def get_power(x,y):
    # fit a power law distribution to the data
    # via https://scipy-cookbook.readthedocs.io/items/FittingData.html
    logx = np.log10(x)
    logy = np.log10(y)
    #logyerr = yerr / ydata
    fitfunc = lambda p, x: p[0] + p[1] * x
    errfunc = lambda p, x, y: (y - fitfunc(p, x))

    pinit = [1.0, -1.0]
    out = optimize.leastsq(errfunc, pinit, args=(logx, logy), full_output=1)
    pfinal = out[0]
    covar = out[1]
    #print(pfinal)
    #print(covar)
    index = pfinal[1]
    amp = 10.0**pfinal[0]
    return (amp,index)
    
def create_animation():
    p = subprocess.Popen(['convert','-delay','50','-loop','0','*.png','animated.gif'])
    p.wait()

def arrayfilter(item,index,mylist):
    return item[index] in mylist
    
def get_contribs(x,y,userlist):
    myusers = []
    for num,user in list(zip(x,y)):
        username = user[0]
        activity = user[1]
        if username in userlist:
            myusers.append((num,username,activity))
    list_contribs = np.array(myusers,dtype=([('num',np.int),('name',np.str_,50),('activity',np.int)]))
    msg_list = np.sum(list_contribs['activity'])
    msg_total = np.sum(y['activity'])
    msg_list_percent = 100*msg_list/msg_total
    contrib_stats = "Steering Dominance: {:.0f}% ({}/{} public msgs)".format(msg_list_percent,msg_list,msg_total)
    return list_contribs,contrib_stats

def analyze_lookback(daysback,daysinterval):
    steeringlist = ["put","the","slack","usernames","of","your","leadership","team","here"]
    for daysago in range(daysback,0,-daysinterval):
        enddate = (datetime.datetime.now()-datetime.timedelta(days=daysago)).date()
        x,y = getlogs(enddate)
        steering_contribs,contrib_stats = get_contribs(x,y,steeringlist)
        #plot_stuff(x,y,steering_contribs,enddate,"{} on {}".format(contrib_stats,enddate))
        plot_stuff(x,y,steering_contribs,enddate,"{} up to {}".format("Slacktivity",enddate),contrib_stats)
        
if __name__ == "__main__":
    analyze_lookback(60,1)
    create_animation()
