from selenium import webdriver
from tkinter import messagebox
import tkinter as tk
import time
import json
import os

import socket    
socket.setdefaulttimeout(20)

class XuexiException(Exception):
    def __init__(self,errlog):
        self.errlog=errlog
    def __str__(self):
        return self.errlog
    
def current_points():
    browser.get(r'https://pc.xuexi.cn/points/my-points.html')
    time.sleep(5)
    try:
        return int(browser.find_elements_by_class_name("my-points-points")[1].text)
    except:
        raise XuexiException('分数获取异常')
    
def get_video_list(browser, have_watch, neednum, *, retry_count = 2):
    #have_watch反向计数，从最后一个视频倒着数have_watch个都已经看过(防止正序观看，更新后计数问题)
    #neednum表示应该返回倒数第have_watch + 1到have_watch + neednum视频的url
    if neednum == 0:
        return []
    url = r'https://www.xuexi.cn/4426aa87b0b64ac671c96379a3a8bd26/db086044562a57b441c24f2af1c8e101.html#1novbsbi47k-5'
    browser.get(url)
    time.sleep(30)
    try:
        browser.find_elements_by_class_name("btn")[5].click()        #翻到最后一页
        count = len(browser.find_elements_by_class_name("innerPic")) #找出最后一个有几个可以观看的(可能不满20个)
        
        if have_watch <= count:                                      #have_watch代表已经看过的，看过的都不看了
            yu = count - have_watch
        else:
            click = int(( have_watch - count + 20) / 20 )            #click代表向前翻click页可以把整页都看过的恰好翻过去
            for _ in range(click):
                browser.find_elements_by_class_name("btn")[1].click()
            yu = ( have_watch - count ) % 20
            yu = 20 - yu
        #yu: 现在代表当前页面正数有yu个可看
        #import pdb;pdb.set_trace()                                  #断点调试
        ls = []
        video_list = browser.find_elements_by_css_selector("._1PcbELBKVoVrF5XKNSE_SF.thePic")
    
    
        up = min(yu, neednum)#当前页面正序最多看up个
        for i in range(up):
            ls.append(video_list[yu - i - 1].get_attribute("data-link-target"))
        if yu < neednum:                                             #如果当前页面能获取少于neednum个
            need = neednum - yu
            browser.find_elements_by_class_name("btn")[1].click()    #到前一个页面再获取
            video_list = browser.find_elements_by_css_selector("._1PcbELBKVoVrF5XKNSE_SF.thePic")
            for i in range(need):
                ls.append(video_list[20 - i - 1].get_attribute("data-link-target"))
    except:
        #防止页面点击后因网络原因未加载完毕即进行页面元素定位导致错误，重试retry_count次
        #try代码块始于从第一次定位元素代码之前，终于最后点击页面后第一次元素定位代码之后
        if retry_count != 0:
            return get_video_list(browser, have_watch, neednum, retry_count - 1)
        raise                                                        #抛出原错误
    return ls                                                        #返回包含neednum个url的列表
        
def get_article_list(browser, have_read, neednum, retry_count = 2):  #与get_video_list函数相似，注释见上
    if neednum == 0:
        return []
    def click_elements_and_append_url_to_ls(elements, ls):           #将获取每一个标题元素，点击弹出新页面，将新页面的url放入ls
        for element in elements:
            element.click()
            browser.switch_to_window(browser.window_handles[1])
            ls.append(browser.current_url)
            browser.close()
            browser.switch_to_window(browser.window_handles[0])

    url = r'https://www.xuexi.cn/7097477a9643eacffe4cc101e4906fdb/9a3668c13f6e303932b5e0e100fc248b.html'
    browser.get(url)
    time.sleep(30)
    try:
        browser.find_elements_by_class_name("btn")[5].click()       #翻到最后一页
        count = len(browser.find_elements_by_class_name("_3wnLIRcEni99IWb4rSpguK"))

        if have_read <= count:
            yu = count - have_read
        else:
            click = int(( have_read - count + 20 ) / 20 )
            for _ in range(click):
                browser.find_elements_by_class_name("btn")[1].click()
            yu = ( have_read - count ) % 20
            yu = 20 - yu
        ls = []
        elements = []
        up = min(yu, neednum)
        article_list = browser.find_elements_by_class_name("_3wnLIRcEni99IWb4rSpguK")
        for i in range(up):
            elements.append(article_list[yu - i -1])                #url被隐藏，直接存储元素，模拟点击后再去新页面获得url

        click_elements_and_append_url_to_ls(elements, ls)
        elements = []
        if yu < neednum:
            need = neednum - yu
            browser.execute_script('document.getElementsByClassName("btn")[1].click()')
            article_list = browser.find_elements_by_class_name("_3wnLIRcEni99IWb4rSpguK")
            for i in range(need):
                elements.append(article_list[20 - i - 1])

        click_elements_and_append_url_to_ls(elements, ls)
    except:
        if retry_count != 0:
            return get_article_list(browser, have_read, neednum, retry_count - 1)
        raise
    
    return ls
    
def xuexi_play_video(browser, url, retry_count = 2):                              #browser 6个每个18/6=3分钟=180秒
    browser.get(url)
    time.sleep(5)
    browser.execute_script('window.scrollBy(0, 1000)')
    try:
        playvideo = browser.find_element_by_class_name("outter")
        try:
            playvideo.click()                                                     #!!!进去后就自动播放了，但是手动进入却不自动播放，自动播放outter元素就被隐藏了，不能点击!!!
        except:
            pass
        #import pdb;pdb.set_trace()
    except:
        if retry_count != 0:
            xuexi_play_video(browser, url, retry_count - 1)
        raise
    time.sleep(200)

def xuexi_read_article(browser, url, retry_count = 2):                            #browser 6篇每个12/6=2分钟=120秒
    browser.get(url)
    time.sleep(0.5)
    try:
        for _ in range(10):
            browser.execute_script('window.scrollBy(0,100)')
            time.sleep(15)
    except:
        if retry_count != 0:
            xuexi_read_article(browser, url, retry_count - 1)
        raise

def check_and_solve(browser, cookies_string, retry_count = 2):                    #主函数
    global have_watch, have_read
    browser.get(r'https://pc.xuexi.cn/points/my-points.html')                     #先进入一个页面才能添加cookies
    browser.delete_all_cookies()
    for cookie in json.loads(cookies_string):
        if 'expiry' in cookie:
            del cookie['expiry']
        browser.add_cookie(cookie)
    browser.get(r'https://pc.xuexi.cn/points/my-points.html')                     #学习强国积分页
    time.sleep(5)
    if browser.current_url != 'https://pc.xuexi.cn/points/my-points.html':
        raise XuexiException("用户登录失败")                                      #编写异常
    points_list = []
    try:
        for element in browser.find_elements_by_class_name("my-points-card-text"):
            text = element.text
            points_list.append(abs(int(text[0]) - int(text[3])))
            
        article_url_neednum = max(points_list[1], points_list[3])
        video_url_neednum   = max(points_list[2], points_list[4])
        
        list_article = get_article_list(browser, have_read, article_url_neednum)
        list_video = get_video_list(browser, have_watch, video_url_neednum)

        for url in list_article:
            xuexi_read_article(browser, url)
            have_read += 1
        for url in list_video:
            xuexi_play_video(browser, url)
            have_watch += 1

        with open('count.txt', 'w') as f:
            f.write(str(have_read) + ',' + str(have_watch))
        if current_points() < 25:
            return False
        return True
    except:
        if retry_count != 0:
            check_and_solve(browser, cookies_string, retry_count - 1)
        raise


def page_loading_timeout(browser, url, time):
    browser.set_page_load_timeout(time)
    try:
        browser.get(url)
    except:
        browser.execute_script("window.stop()")

def callback1():#登录并获取cookies
    page_loading_timeout(browser, 'https://pc.xuexi.cn/points/login.html', 10)
    browser.execute_script('window.scrollBy(0,1000)')
    messagebox.showinfo('提示', '网页中扫码登录后点击确定，否则将获取错误cookies')  #阻塞主进程，等待用户登录并确认后再运行后面代码
    time.sleep(3)
    browser.refresh()
    cookies_list = browser.get_cookies()
    with open(r'cookies.txt', 'w') as f:
        f.write(json.dumps(cookies_list))
    messagebox.showinfo('提示', 'cookies已保存')
    
def callback2():#运行，通过已有cookies
    try:
        if not os.path.exists('cookies.txt'):
            raise XuexiException('用户未登录')
        with open('cookies.txt', 'r') as f:                                         #获得cookies
            cookies_string = f.read();
            old_points = 0
            while True:
                if check_and_solve(browser, cookies_string) == False:
                    cur_points = current_points()
                    if cur_points == old_points:
                        with open('count.txt', 'w') as f:
                            f.write(str(have_read) + ',' + str(have_watch))
                        raise XuexiException('可能出错了，需要检查源码')
                    else:
                        old_points = cur_points
                else:
                    break 
    except XuexiException as e:
        messagebox.showwarning('警告', str(e))
    else:
        messagebox.showinfo('提示', '有惊无险, 25分到手')
    finally:
        with open('count.txt', 'w') as f:
            f.write(str(have_read) + ',' + str(have_watch))
        

browser = webdriver.Chrome()
with open('count.txt', 'r') as f:
    have_read, have_watch = map(int, f.read().split(','))
#callback1()
'''
while True:
    if input('kkdkdkd:') == '1':
        callback1()
    else:
        callback2()
'''
root = tk.Tk()
root.title('title')
root.geometry('180x200')
photo = tk.PhotoImage(file = '1.gif')
tk.Label(root, image = photo).pack(side = 'top')
tk.Button(root, text = '登录', command = callback1).pack(side = 'left', padx = 5, pady = 5)
tk.Button(root, text = '运行', command = callback2).pack(side = 'right', padx = 5, pady = 5)
root.mainloop()

browser.quit()

