# !/usr/bin/python
from platform import system
from kivy.app import App
from kivy.config import Config
from kivy.uix.accordion import Accordion
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
from kivy.uix.textinput import TextInput

import os
import sys
import argparse
import time
from subprocess import PIPE, Popen, STDOUT
from threading import Thread
from Queue import Queue, Empty
import shutil

from lib.checklastblock import CheckLastBlock
from lib.savewallet import storeWallet
from lib.transferfunds import transferfundsrpccall


# Set POSIX argument for linux for something...
ON_POSIX = 'posix' in sys.builtin_module_names


# parser gets command line args
parser = argparse.ArgumentParser()
parser.parse_args()


# define functions to read output streams
def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


def read_output(process, stdout, queue):
    while True:
        out = stdout.readline()
        #print("Process is: "+process.poll())
        if out == '' and process.poll() != None:
            break
        if out != '':
            line = out.rstrip()
            queue.put_nowait(line)
            sys.stdout.flush()


# Function to split tx output lines
def txSplit(line):
    split_line = line.split(': ')
    try:
        amount = float(split_line[1].split(',')[0])
        tx = split_line[2].strip('<>')
        date = split_line[0].split('.')[0]
        return amount, tx, date
    except ValueError:
        return "Error", "Error", "Error"
    except IndexError:
        return "Error", "Error", "Error"


class MarkupLabel(Label):
    """ Label class with markup on by default """
    pass


class TabTextInput(TextInput):
    """ Tab or enter to next TextInput class """

    def __init__(self, *args, **kwargs):
        self.next = kwargs.pop('next', None)
        super(TabTextInput, self).__init__(*args, **kwargs)

    def set_next(self, next):
        self.next = next

    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        if key in (9, 13) and self.next is not None:
            self.next.focus = True
            self.next.select_all()
        else:
            super(TabTextInput, self)._keyboard_on_key_down(window, keycode, text, modifiers)


class InitialPopup(Popup):
    """ Initial popup widget """

    def loadWalletPopup(self):
        self.dismiss()
        lwp = LoadWalletPopup()
        lwp.open()

    def createWalletPopup(self):
        self.dismiss()
        cwp = CreateWalletPopup()
        cwp.open()

    def quit(self):
        sys.exit(0)


class CreateWalletPopup(Popup):
    """ Wallet creation screen popup """
    wallet_name = ObjectProperty()
    wallet_pw = ObjectProperty()
    repeat_wallet_pw = ObjectProperty()

    def createWallet(self):
        electrum_coming = False
        wallet_name = self.wallet_name.text
        wallet_pw = self.wallet_pw.text
        if self.wallet_pw.text == self.repeat_wallet_pw.text:
            p = Popen(["simplewallet", "--generate-new-wallet",
                       "./" + wallet_name.replace('.', '') + "_walletData/" + wallet_name,
                       "--password", wallet_pw],
                      stdout=PIPE,
                      stdin=PIPE,
                      bufsize=1,
                      close_fds=ON_POSIX)
            if not os.path.exists('./{0}_walletData'.format(wallet_name.replace('.', ''))):
                os.mkdir('./{0}_walletData'.format(wallet_name.replace('.', '')))
            else:
                sys.exit(7777)
            q = Queue()
            t = Thread(target=enqueue_output, args=(p.stdout, q))
            t.daemon = True  # thread dies with the program
            t.start()
            t_start = time.time()
            while time.time() - t_start < 2:
                try:
                    line = q.get_nowait()  # or q.get(timeout=.1)
                    if "new wallet:" in line:
                        address = line.rstrip().split(': ')[1]
                    if "view key:" in line:
                        view_key = line.rstrip().split(': ')[1]
                    if 130 < len(line.rstrip()) < 350:
                        electrum = line.rstrip()
                    if "PLEASE NOTE:" in line:
                        electrum_coming = line.rstrip()
                    print("simplewallet output:", line.rstrip())
                except Empty:
                    # print('no output yet')
                    pass
                else:  # got line
                    # print(line)
                    pass
                    # time.sleep(0.1)
            p.kill()
            # os.system("taskkill /im simplewallet.exe /f")
            # print(p.pid)
            with open('./{0}_walletData/info.txt'.format(wallet_name.replace('.', '')), 'w') as f:
                f.write("Name:\n{0}\n\nAddress:\n{1}\n\nView key:\n{2}\n\nElectrum seed:\n{3}".format(
                    wallet_name, address, view_key, electrum))
            with open("./CONFIG.file", 'w') as f:
                f.write(wallet_name)
            self.dismiss()
            content = Button(
                text="Your wallet has been created in the local directory {0}_walletData\nThe info.txt document in that folder contains your wallet recovery seed.\nPlease keep this seed safe, you can restore a corrupted/lost wallet with it.\nSomeone else can also bypass your password and steal your XMR with it.\nI suggest deleting or encrypting this file.".format(
                    wallet_name))
            walletCreatedPopup = Popup(title="Wallet created window",
                                       content=content)
            content.bind(on_press=walletCreatedPopup.dismiss)
            walletCreatedPopup.open()
            App.get_running_app().root.launchWallet(wallet_name, wallet_pw)
        else:
            content = Button(text="Check passwords!!!\nClick to dismiss")
            pwErrorPopup = Popup(title="Password match error window",
                                 content=content)
            content.bind(on_press=pwErrorPopup.dismiss)
            pwErrorPopup.open()


class LoadWalletPopup(Popup):
    """ Wallet loading screen popup """
    wallet_path = ObjectProperty()
    wallet_pw = ObjectProperty()
    repeat_wallet_pw = ObjectProperty()

    def loadWallet(self):
        split_name = os.path.split(self.wallet_path.text)[1].split('.')
        wallet_name = '.'.join(tuple(split_name[0:len(split_name) - 1]))
        print(split_name, wallet_name)
        wallet_pw = self.wallet_pw.text
        wallet_error = False
        if self.wallet_pw.text == self.repeat_wallet_pw.text:
            p = Popen(["simplewallet", "--wallet-file",
                       self.wallet_path.text,
                       "--password", wallet_pw],
                      stdout=PIPE,
                      stdin=PIPE,
                      bufsize=1,
                      close_fds=ON_POSIX)
            q = Queue()
            t = Thread(target=enqueue_output, args=(p.stdout, q))
            t.daemon = True  # thread dies with the program
            t.start()
            t_start = time.time()
            while time.time() - t_start < 2:
                try:
                    line = q.get_nowait()  # or q.get(timeout=.1)
                    print("simplewallet output:", line.rstrip())
                    if "Opened wallet: " in line.rstrip():
                        address = line.rstrip().split(": ")[1]
                    if "Error: failed" in line.rstrip():
                        wallet_error = True
                except Empty:
                    # print('no output yet')
                    pass
                else:  # got line
                    pass
            p.kill()
        if not wallet_error:
            if not os.path.exists("./{0}_walletData".format(wallet_name.replace('.', ''))):
                os.mkdir("./{0}_walletData".format(wallet_name.replace('.', '')))
            with open("./CONFIG.file", 'w') as f:
                f.write(wallet_name)
            with open("./{0}_walletData/{1}.address.txt".format(wallet_name.replace('.', ''), wallet_name), 'w') as f:
                f.write(address)
            shutil.copyfile(self.wallet_path.text,
                            "./{0}_walletData/{1}.keys".format(wallet_name.replace('.', ''), wallet_name))
            self.dismiss()
            content = Button(
                text="Your wallet keys file has been copied to the local directory {0}_walletData\nThe original has not been disturbed.".format(
                    wallet_name))
            walletCopiedPopup = Popup(title="Wallet keys copied window",
                                      content=content)
            content.bind(on_press=walletCopiedPopup.dismiss)
            walletCopiedPopup.open()
            App.get_running_app().root.launchWallet(wallet_name, wallet_pw)
        else:
            content = Button(text="Wallet import error!\nClick to start over")
            pwErrorPopup = Popup(title="Wallet import error window",
                                 content=content)
            content.bind(on_press=pwErrorPopup.dismiss)
            ip = InitialPopup()
            content.bind(on_press=ip.open)
            pwErrorPopup.open()


class PasswordPopup(Popup):
    """ Popup class to get pw on launch with CONFIG.file """
    wallet_pw = ObjectProperty()
    walletname_label = ObjectProperty()

    def __init__(self, wallet_name):
        super(PasswordPopup, self).__init__()
        self.wallet_name = wallet_name
        if not App.get_running_app().root.wallet_error:
            self.walletname_label.text = "Please enter your password for {0} account:".format(self.wallet_name)
        if App.get_running_app().root.wallet_error:
            self.walletname_label.text = "There seems to be a problem with binary file,\nPlease enter your password to attempt rebuild of {0} account:".format(
                self.wallet_name)

    def launchWallet(self):
        wallet_pw = self.wallet_pw.text
        App.get_running_app().root.launchWallet(self.wallet_name, wallet_pw)
        self.dismiss()


class TransferPopup(Popup):
    """ Popup class to initiate XMR transfer """
    transfer_popup_label = ObjectProperty()

    def __init__(self, amount, address, mixin, paymentid):
        super(TransferPopup, self).__init__()
        self.amount = amount
        self.address = address
        self.mixin = mixin
        self.paymentid = paymentid
        self.popuptext = "Are you sure you want to send {0:0.9f} XMR\n to [size=8]{1}[/size]\n with mixin count {2} and payment id [size=8]{3}[/size]".format(
            float(amount), address, mixin, paymentid)
        self.transfer_popup_label.text = self.popuptext

    def transfer(self):
        txid = transferfundsrpccall(self.amount, self.address, self.mixin, self.paymentid)
        txid_popup = TxIDPopup(txid)
        txid_popup.open()


class TxIDPopup(Popup):
    txid_label = ObjectProperty()
    def __init__(self, txid):
        super(TxIDPopup, self).__init__()
        self.txid = txid
        self.txid_label.text = "TxID: [ref=txid]{0}[/ref]\n(Click TxID to copy to clipboard)".format(txid)

    def selecttxid(self):
        Clipboard.put(self.txid)


class RootWidget(Accordion):
    """Root Kivy accordion widget class"""
    wallet_error = None
    # Transfer XMR id items
    address_input_textinput = ObjectProperty()
    amount_input_textinput = ObjectProperty()
    mixin_input_textinput = ObjectProperty()
    paymentid_input_textinput = ObjectProperty()
    # Wallet account id items
    wallet_account_label = ObjectProperty()
    wallet_address_label = ObjectProperty()
    unlocked_balance_label = ObjectProperty()
    total_balance_label = ObjectProperty()
    calculated_balance_label = ObjectProperty()
    # Daemon id items
    daemon_server_textinput = ObjectProperty()
    blockheight_label = ObjectProperty()
    last_reward_label = ObjectProperty()
    last_block_time_label = ObjectProperty()
    time_since_last_label = ObjectProperty()
    wallet_block_label = ObjectProperty()
    blockheight = 0
    # Process, queue, and thread variables
    daemon_queue = Queue()
    daemon_thread = None
    wallet_process = None
    wallet_queue = Queue()
    wallet_thread = None
    # Other variables
    calculated_balance = 0.0
    total_balance = 0.0
    unlocked_balance = 0.0
    temp_tx_amount = 0.0
    temp_tx_hash = ""
    temp_tx_paymentid = ""
    wallet_save_time = None

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.daemon_thread = Thread(target=self.checkDaemonStatus,
                                    args=(self.daemon_queue, self.daemon_server_textinput.text))
        self.daemon_thread.daemon = True
        self.daemon_thread.start()
        if os.path.isfile('./CONFIG.file'):
            with open('./CONFIG.file', 'r') as f:
                self.wallet_name = f.read().rstrip()
                print(self.wallet_name)
            Clock.schedule_once(self.initialPassword, 0.5)
        else:
            Clock.schedule_once(self.initialConfig, 0.5)
        Clock.schedule_interval(self.checkDaemon, 5)


    def initialConfig(self, dt):
        ip = InitialPopup()
        ip.open()

    def initialPassword(self, dt):
        gp = PasswordPopup(self.wallet_name)
        gp.open()

    def checkDaemonStatus(self, daemon_queue, server):
        """Class to be threaded for checking bitmonerod status"""
        # print(server)
        height, reward, timesince, localtime = CheckLastBlock(server + "/json_rpc")
        daemon_queue.put((height, reward, timesince, localtime))
        # print("sleeping")
        time.sleep(1)
        self.checkDaemonStatus(daemon_queue, self.daemon_server_textinput.text)

    def checkDaemon(self, dt):
        try:
            height, reward, timesince, localtime = self.daemon_queue.get_nowait()
            self.blockheight = int(height)
            self.blockheight_label.text = "[b][color=00ffff]{0}[/b][/color]".format(height)
            self.last_reward_label.text = "[b][color=00ffff]{0:.2f}[/b][/color] XMR".format(reward * 1e-12)
            self.last_block_time_label.text = "[b][color=00ffff]{0}[/b][/color]".format(localtime)
            self.time_since_last_label.text = "[b][color=00ffff]{0:.0f}[/b][/color] seconds".format(timesince)
        except:
            pass

    def launchWallet(self, wallet_name, wallet_pw):
        with open("./{0}_walletData/{1}.address.txt".format(wallet_name.replace('.', ''), wallet_name), 'r') as f:
            self.address = f.read().rstrip()
        self.wallet_account_label.text = "[b][color=00ffff]{0}[/b][/color]".format(wallet_name)
        self.wallet_address_label.text = "[b][color=00ffff][ref=Address]{0}[/ref][/b][/color]".format(self.address)
        if not os.path.isfile("./{0}_walletData/{1}".format(wallet_name.replace('.', ''), wallet_name)):
            self.wallet_process = Popen(["simplewallet.exe", "--wallet-file", "./{0}_walletData/{1}".format(
                                          wallet_name.replace('.', ''), wallet_name), "--password", wallet_pw],
                                          stdin=PIPE,
                                          stdout=PIPE,
                                          stderr=STDOUT,
                                          bufsize=1)
            self.wallet_process.communicate(input="exit\r\n")
            self.wallet_process.kill()
        # try:
        #     system("taskkill /im simplewallet.exe /f")
        # except:
        #     print("Simplewallet.exe not running")
        if os.path.isfile("./{0}_walletData/tx.txt".format(wallet_name.replace('.', ''))):
            with open("./{0}_walletData/tx.txt".format(wallet_name.replace('.', ''), 'r')) as previous_txs:
                txs = previous_txs.read().split('\n')
            for idx, line in enumerate(txs):
                this_amount, this_tx, this_date = txSplit(line)
                if idx < len(txs) - 1:
                    next_amount, next_tx, date = txSplit(txs[idx+1])
                else:
                    next_amount, next_tx, date = "Done", "Done", "Done"
                if this_tx != next_tx and self.temp_tx_amount == 0.0:
                    if "Received" in line:
                        l = Label(text="Received {0:0.3f} XMR on {1} in tx: {2}".format(this_amount, this_date, this_tx),
                                  size_hint_y=None, height=15, font_size=9)
                        self.ids.tx_list.add_widget(l)
                        self.calculated_balance += this_amount
                    elif "Spent" in line:
                        l = Label(text="Spent {0:0.3f} XMR on {1} in tx: {2}".format(this_amount, this_date, this_tx),
                                  size_hint_y=None, height=15, font_size=9)
                        self.ids.tx_list.add_widget(l)
                        self.calculated_balance -= this_amount
                elif this_tx == next_tx and self.temp_tx_amount == 0.0:
                    self.temp_tx_amount += this_amount + next_amount
                elif this_tx == next_tx and self.temp_tx_amount != 0.0:
                    self.temp_tx_amount += next_amount
                elif this_tx != next_tx and self.temp_tx_amount != 0.0:
                    if "Received" in line:
                        l = Label(text="Received {0:0.3f} XMR on {1} in tx: {2}".format(this_amount, this_date, this_tx),
                                  size_hint_y=None, height=15, font_size=9)
                        self.ids.tx_list.add_widget(l)
                        self.calculated_balance += self.temp_tx_amount
                    elif "Spent" in line:
                        l = Label(text="Spent {0:0.3f} XMR on {1} in tx: {2}".format(this_amount, this_date, this_tx),
                                  size_hint_y=None, height=15, font_size=9)
                        self.ids.tx_list.add_widget(l)
                        self.calculated_balance -= self.temp_tx_amount
                    self.temp_tx_amount = 0.0
        self.temp_tx_amount = 0.0
        self.calculated_balance_label.text = "[b][color=00ffff]{0:.3f}[/b][/color]".format(self.calculated_balance)
        self.wallet_process = Popen(["simplewallet", "--wallet-file", "./{0}_walletData/{1}.keys".format(
                                     wallet_name.replace('.', ''), wallet_name), "--password", wallet_pw,
                                     "--daemon-address", self.daemon_server_textinput.text, "--rpc-bind-port", "19091"],
                                      stdin=PIPE,
                                      stdout=PIPE,
                                      stderr=STDOUT,
                                      bufsize=1)
        self.wallet_thread = Thread(target=read_output,
                                    args=(self.wallet_process, self.wallet_process.stdout, self.wallet_queue))
        # self.wallet_thread = Thread(target=enqueue_output,
        #                             args=(self.wallet_process.stdout, self.wallet_queue))
        self.wallet_thread.daemon = True  # thread dies with the program
        self.wallet_thread.start()
        Clock.schedule_interval(self.readWalletQueue, .01)
        # Clock.schedule_interval(self.saveWallet, 60)

    def readWalletQueue(self, dt):
        print(self.wallet_thread.is_alive)
        try:
            print("trying")
            newLine = self.wallet_queue.get_nowait()
            # with open("rpcwallet.log", 'a') as logfile:
            # logfile.write(newLine+'\n')
            print newLine
            if "Wallet initialize failed: failed to read file" in newLine:
                self.wallet_thread.join()
                self.wallet_error = True
                os.remove("./{0}_walletData/{1}".format(self.wallet_name.replace('.', ''), self.wallet_name))
                Clock.schedule_once(self.initialPassword, 0.5)
            if "height:" in newLine:
                height = newLine.split(", ")[1].split(": ")[1]
                self.wallet_block_label.text = "[b][color=00ffff]{0}[/b][/color] of [b][color=00ffff]{1}[/b][/color]".format(
                    height, self.blockheight)
            elif "height " in newLine:
                height = newLine.split(", ")[1].split(" ")[1]
                self.wallet_block_label.text = "[b][color=00ffff]{0}[/b][/color] of [b][color=00ffff]{1}[/b][/color]".format(
                    height, self.blockheight)
            elif "Refresh done," in newLine:
                print("refresh done")
                split_line = newLine.split(',')
                self.total_balance = float(split_line[2].split(': ')[1])
                self.unlocked_balance = float(split_line[3].split(': ')[1])
                self.total_balance_label.text = "[b][color=00ffff]{0:.3f}[/b][/color]".format(self.total_balance)
                self.unlocked_balance_label.text = "[b][color=00ffff]{0:.3f}[/b][/color]".format(self.unlocked_balance)
                if not self.wallet_save_time:
                    print("First save launching!")
                    Clock.schedule_once(self.saveWallet, 0.1)
                    self.wallet_save_time = time.time()
                    print("Wallet saved at: {0}".format(self.wallet_save_time))
                if self.wallet_save_time:
                    if time.time() - self.wallet_save_time > 1800:
                        Clock.schedule_once(self.saveWallet, 0.1)
                        print(time.time(), self.wallet_save_time, "saving")
                        self.wallet_save_time = time.time()
            elif "Received money" in newLine and "with tx" in newLine:
                with open("./{0}_walletData/tx.txt".format(self.wallet_name), 'a') as tx_file:
                    this_amount, this_tx, this_date = txSplit(newLine)
                    tx_file.write(newLine + '\n')
                    self.calculated_balance += this_amount
                    self.calculated_balance_label.text = "[b][color=00ffff]{0:.3f}[/b][/color]".format(
                        self.calculated_balance)
                    l = Label(text="Received {0:0.3f} XMR on {1} in tx: {2}".format(this_amount, this_date, this_tx),
                              size_hint_y=None, height=15, font_size=9)
                    self.ids.tx_list.add_widget(l)
            elif "Spent money" in newLine and "with tx" in newLine:
                with open("./{0}_walletData/tx.txt".format(self.wallet_name), 'a') as tx_file:
                    this_amount, this_tx, this_date = txSplit(newLine)
                    tx_file.write(newLine + '\n')
                    self.calculated_balance -= this_amount
                    l = Label(text="Spent {0:0.3f} XMR on {1} in tx: {2}".format(this_amount, this_date, this_tx),
                              size_hint_y=None, height=15, font_size=9)
                    self.ids.tx_list.add_widget(l)
            # elif "Payment found" in newLine:
            #     with open("./{0}_walletData/tx.txt".format(self.wallet_name), 'a') as tx_file:
            #         tx_file.write(newLine + '\n')
        except Empty:
            pass
        # if not self.wallet_thread.is_alive():
        #     print("dead")
        #     self.wallet_thread.start()
        #     Clock.schedule_interval(self.readWalletQueue, 0.01)

    def saveWallet(self, dt):
        print("Launching save thread")
        save_thread = Thread(target=storeWallet)
        save_thread.daemon = True
        save_thread.start()
        save_thread.join()
        print("Finished save thread")

    def selectAddress(self):
        """copy address to clipboard when user clicks"""
        print('User clicked on ', self.address)
        self.daemon_server_textinput.copy(self.address)

    def transferfunds(self):
        """initiate transfer of funds to new address"""
        try:
            float(self.amount_input_textinput.text)
            tp = TransferPopup(self.amount_input_textinput.text, self.address_input_textinput.text,
                               self.mixin_input_textinput.text, self.paymentid_input_textinput.text)
            tp.open()
        except ValueError:
            print("no,no")


class KVNewApp(App):
    def build(self):
        return RootWidget()


if __name__ == '__main__':
    Config.set('kivy', 'exit_on_escape', 0)
    Config.set('kivy', 'window_icon', "./lilicon.ico")
    KVNewApp().run()
    try:
        App.get_running_app().root.wallet_process.kill()
    except:
        print("Wallet process not running")
    # try:
    #     system("taskkill /im simplewallet.exe /f")
    # except:
    #     print("Simplewallet.exe not running")
