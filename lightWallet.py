# !/usr/bin/python
from kivy.app import App
from kivy.config import Config
from kivy.uix.accordion import Accordion
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

import os
import sys
import argparse
import time
import datetime
import re
import random
import shutil

from subprocess import PIPE, Popen, STDOUT
from threading import Thread
from Queue import Queue, Empty

from lib.checklastblock import checkLastBlock
from lib.savewallet import storeWallet
from lib.transferfunds import transferFundsRPCCall
from lib.checkbalance import checkBalanceSimplewallet
from lib.gettransfers import getTransfers


# Set POSIX argument for linux for something...
ON_POSIX = 'posix' in sys.builtin_module_names

# Donation wallet addy
# donate_CMC_address = "4ATxc8rJjG62ToWqCibuPv7kY9ikds3b3JmRHYqAAymEdhwBGfhtwRgMuHF9bsn18f4wXrK93cw6xdsVCJJwizkiHeUuJKB"
donate_core_address = "46BeWrHpwXmHDpDEUmZBWZfoQpdc6HaERCNmx1pEYL2rAcuwufPN9rXHHtyUA4QVy66qeFQkn6sfK8aHYjA3jk3o1Bv16em"

# URLs for servers
moneroclub_URL = "http://node.moneroclub.com:8880"
localhost_URL = "http://localhost:18081"
daemon_URL = moneroclub_URL

# parser gets command line args
parser = argparse.ArgumentParser()
parser.parse_args()


# define functions to read output streams
def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


# Check if a string is hex only
def hex_match(strg, search=re.compile(r'[^a-fA-F0-9]').search):
    return not bool(search(strg))


# Generate random hex strings for payment id
def gen_paymentid():
   return ''.join([random.choice('0123456789ABCDEF') for x in range(64)])


# Function to kill shit on windows
def windows_task_killer(pid):
    try:
        os.system("taskkill /F /T /PID {0}".format(pid))
        print("Simplewallet process killed with PID {0} killed".format(pid))
    except:
        print("This {0} simplewallet instance isn't running".format(pid))
    try:
        os.system("tskill {0}".format(pid))
        print("Simplewallet process killed with PID {0} killed".format(pid))
    except:
        print("This {0} simplewallet instance isn't running or no tskill".format(pid))


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
        if key == 9 and self.next is not None:
            self.next.focus = True
            self.next.select_all()
        else:
            super(TabTextInput, self)._keyboard_on_key_down(window, keycode, text, modifiers)


class AsciiInput(TabTextInput):
    """ TabTextInput class that only allows ascii input"""
    pattern = re.compile('[^0-9a-zA-Z+_=;.\-\(\)\[\]{}]')
    def insert_text(self, substring, from_undo=False):
        pattern = self.pattern
        s = re.sub(pattern, '', substring)
        return super(AsciiInput, self).insert_text(s, from_undo=from_undo)


class AsciiSlashInput(TabTextInput):
    """ TabTextInput class that only allows ascii input and slashes"""
    pattern = re.compile('[^0-9a-zA-Z+_=;:/.\-\(\)\[\]{}\\\]')
    def insert_text(self, substring, from_undo=False):
        pattern = self.pattern
        s = re.sub(pattern, '', substring)
        return super(AsciiSlashInput, self).insert_text(s, from_undo=from_undo)


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

    def __init__(self, *args, **kwargs):
        super(CreateWalletPopup, self).__init__(*args, **kwargs)

    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        print(key, key_str)
        if key in (13, 271):
            self.submitForm()
        else:
            super(CreateWalletPopup, self)._keyboard_on_key_down(window, keycode, text, modifiers)

    def submitForm(self):
        electrum_coming, electrum_1, electrum_2, electrum_3, electrum_4 = None, None, None, None, None
        wallet_name = self.wallet_name.text
        wallet_pw = self.wallet_pw.text
        wallet_dir = os.path.join(App.get_running_app().root.data_dir, "{0}_walletData".format(wallet_name.replace('.', '')))
        wallet_file = os.path.join(wallet_dir, wallet_name)
        if self.wallet_pw.text == self.repeat_wallet_pw.text:
            if not os.path.exists(wallet_dir):
                os.mkdir(wallet_dir)
            else:
                sys.exit(7777)
            p = Popen(["simplewallet", "--generate-new-wallet", wallet_file, "--password", wallet_pw],
                      stdout=PIPE,
                      stdin=PIPE,
                      bufsize=1,
                      close_fds=ON_POSIX)
            q = Queue()
            t = Thread(target=enqueue_output, args=(p.stdout, q))
            t.daemon = True  # thread dies with the program
            p.stdin.write(str("0\r\n"))
            p.stdin.flush()
            t.start()
            t_start = time.time()
            while time.time() - t_start < 2:
                try:
                    line = q.get_nowait()  # or q.get(timeout=.1)
                    if "new wallet:" in line:
                        address = line.rstrip().split(': ')[2]
                    if "view key:" in line:
                        view_key = line.rstrip().split(': ')[1]
                    if electrum_3:
                        electrum_line_4 = line.rstrip()
                        electrum_3 = False
                    if electrum_2:
                        electrum_line_3 = line.rstrip()
                        electrum_3 = True
                        electrum_2 = False
                    if electrum_1:
                        electrum_line_2 = line.rstrip()
                        electrum_2 = True
                        electrum_1 = False
                    if electrum_coming:
                        electrum_1 = True
                        electrum_coming = False
                    if 130 < len(line.rstrip()) < 350:
                        electrum_coming = True
                        print(line.rstrip())
                    print("simplewallet output:", line.rstrip())
                except Empty:
                    # print('no output yet')
                    pass
                else:  # got line
                    # print(line)
                    pass
                    # time.sleep(0.1)
            if sys.platform == 'win32':
                try:
                    p.kill()
                    print("Simplewallet process killed")
                except:
                    print("Wallet process not running")
                try:
                    windows_task_killer(App.get_running_app().root.wallet_process.pid)
                except:
                    print("Nonetype error")
            with open(os.path.join(wallet_dir, "info.txt"), 'w') as f:
                f.write("Name:\n{0}\n\nAddress:\n{1}\n\nView key:\n{2}\n\nElectrum seed:\n{3}".format(
                    wallet_name, address, view_key, electrum_line_2+' '+electrum_line_3+' '+electrum_line_4))
            with open(os.path.join(App.get_running_app().root.data_dir, "CONFIG.file"), 'w') as f:
                f.write("Account name= " + wallet_name + "\n")
                f.write("Bitmonerod daemon server= {0}".format(daemon_URL))
            self.dismiss()
            confirm_box = BoxLayout(orientation='vertical')
            confirm_label = Label(
                text="Your wallet has been created in the\nMy Documents/lightWallet/{0}_walletData directory.\nThe info.txt document in that folder contains your wallet recovery seed.\nPlease keep this seed safe, you can restore a corrupted/lost wallet with it.\nSomeone else can also bypass your password and steal your XMR with it.\nI suggest deleting or encrypting this file.\nClick to dismiss.".format(
                    wallet_name))
            confirm_button = Button(text="Click to dismiss", size_hint_y=0.2)
            confirm_box.add_widget(confirm_label)
            confirm_box.add_widget(confirm_button)
            walletCreatedPopup = Popup(title="Wallet created window", content=confirm_box, size_hint=(0.75, 0.75), auto_dismiss=False)
            confirm_button.bind(on_press=walletCreatedPopup.dismiss)
            walletCreatedPopup.open()
            App.get_running_app().root.daemon_thread = Thread(target=App.get_running_app().root.checkDaemonStatus,
                                        args=(App.get_running_app().root.daemon_queue, daemon_URL))
            App.get_running_app().root.daemon_thread.daemon = True
            App.get_running_app().root.daemon_thread.start()
            App.get_running_app().root.launchWallet(wallet_name, wallet_pw)
            App.get_running_app().root.daemon_server_textinput.text = daemon_URL
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

    def submitForm(self):
        split_name = os.path.split(self.wallet_path.text)[1].split('.')
        wallet_name = '.'.join(tuple(split_name[0:len(split_name) - 1]))
        print(split_name, wallet_name)
        wallet_dir = os.path.join(App.get_running_app().root.data_dir, "{0}_walletData".format(wallet_name.replace('.', '')))
        wallet_file = os.path.join(wallet_dir, wallet_name)
        wallet_pw = self.wallet_pw.text
        wallet_error = True
        if self.wallet_pw.text == self.repeat_wallet_pw.text:
            if not os.path.exists(wallet_dir):
                os.mkdir(wallet_dir)
            else:
                sys.exit(7777)
            p = Popen(["simplewallet", "--wallet-file", self.wallet_path.text, "--password", wallet_pw],
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
            if sys.platform == 'win32':
                try:
                    p.kill()
                    print("Simplewallet process killed")
                except:
                    print("Wallet process not running")
                try:
                    windows_task_killer(App.get_running_app().root.wallet_process.pid)
                except:
                    print("Nonetype error")
            wallet_error = False
        if not wallet_error:
            if not os.path.exists(wallet_dir):
                os.mkdir(wallet_dir)
            with open(os.path.join(App.get_running_app().root.data_dir, "CONFIG.file"), 'w') as f:
                f.write("Account name= " + wallet_name + "\n")
                f.write("Bitmonerod daemon server= {0}".format(daemon_URL))
            with open(os.path.join(wallet_dir, wallet_name+".address.txt"), 'w') as f:
                f.write(address)
            shutil.copyfile(self.wallet_path.text, os.path.join(wallet_dir, wallet_name+".keys"))
            self.dismiss()
            content = Button(
                text="Your wallet keys file has been copied to the\nMy Documents/lightWallet/{0}_walletData directory.\nThe original has not been disturbed.\nClick to dismiss.".format(
                    wallet_name))
            walletCopiedPopup = Popup(title="Wallet keys copied window", content=content, size_hint=(0.75, 0.75))
            content.bind(on_press=walletCopiedPopup.dismiss)
            App.get_running_app().root.daemon_server_textinput.text = daemon_URL
            walletCopiedPopup.open()
            App.get_running_app().root.daemon_thread = Thread(target=App.get_running_app().root.checkDaemonStatus,
                                        args=(App.get_running_app().root.daemon_queue, daemon_URL))
            App.get_running_app().root.daemon_thread.daemon = True
            App.get_running_app().root.daemon_thread.start()
            App.get_running_app().root.launchWallet(wallet_name, wallet_pw)
        else:
            content = Button(text="Wallet import error!\nClick to start over")
            pwErrorPopup = Popup(title="Wallet import error window", content=content, size_hint=(0.75, 0.75))
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
            if not App.get_running_app().root.incorrect_password:
                self.walletname_label.text = "Please enter your password for {0} account:".format(self.wallet_name)
        if App.get_running_app().root.wallet_error:
            self.walletname_label.text = "There seems to be a problem with binary file,\nPlease enter your password to attempt rebuild of {0} account:".format(
                self.wallet_name)
        if App.get_running_app().root.incorrect_password:
            self.walletname_label.text = "It seems you've entered an incorrect password,\nPlease re-enter your password to open {0} account:".format(
                self.wallet_name)

    def submitForm(self):
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
        self.popuptext = "Are you sure you want to send {0:0.4f} XMR\n to [size=9]{1}[/size]\n with mixin count {2} and payment id [size=9]{3}[/size]\n\nAn additional fee of 0.01-0.2 XMR will be required.".format(
            float(amount), address, mixin, paymentid)
        self.transfer_popup_label.text = self.popuptext

    def transfer(self):
        return_boolean, return_value = transferFundsRPCCall(self.amount, self.address, self.mixin, self.paymentid)
        txid_popup = TxIDPopup(return_boolean, return_value, self.amount, self.address, self.mixin, self.paymentid)
        txid_popup.open()


class TxIDPopup(Popup):
    address_popup_label = ObjectProperty()
    paymentid_popup_label = ObjectProperty()
    txid_popup_label = ObjectProperty()
    def __init__(self, return_boolean, return_value, amount, address, mixin, paymentid):
        super(TxIDPopup, self).__init__()
        if return_boolean:
            self.address_popup_label.text = "Successfully sent {0:.3f} XMR\nto [ref=address]{1}[/ref]\n(Click address to copy to clipboard)".format(amount, address)
            self.paymentid_popup_label.text = "Using mixin count {0}\nand payment id: [ref=paymentid]{1}[/ref]\n(Click payment id to copy to clipboard)".format(mixin, paymentid)
            self.txid_popup_label.text = "TxID: [ref=txid]{0}[/ref]\n(Click TxID to copy to clipboard)".format(return_value)
            self.txid = return_value
            self.address = address
            self.paymentid = paymentid
        else:
            self.txid_popup_label.text = "Transaction error! Error message:\n{0}\nPlease try again by (and maybe lower mixin or amount sent).".format(return_value)

    def selectaddress(self):
        Clipboard.put(self.address)
    def selectpaymentid(self):
        Clipboard.put(self.paymentid)
    def selecttxid(self):
        Clipboard.put(self.txid)


class DonateCMC(Popup):
    donation_amount_CMC = ObjectProperty()

    def __init__(self):
        super(DonateCMC, self).__init__()

    def make_donation(self):
        App.get_running_app().root.transferfunds(donate_CMC_address, 0., self.donation_amount_CMC.text, gen_paymentid())
        self.dismiss()


class DonateCore(Popup):
    donation_amount_core = ObjectProperty()

    def __init__(self):
        super(DonateCore, self).__init__()

    def make_donation(self):
        App.get_running_app().root.transferfunds(donate_core_address, 0., self.donation_amount_core.text, gen_paymentid())
        self.dismiss()


class RootWidget(Accordion):
    """Root Kivy accordion widget class"""
    wallet_error = None
    incorrect_password = False
    data_dir = os.path.join(os.path.expanduser('~'), "Documents", "lightWallet")
    # Tx list items
    # tx_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    root_widget = ObjectProperty()
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
    wallet_savetime_label = ObjectProperty()
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
    balance_queue = Queue()
    balance_thread = None
    wallet_process = None
    wallet_queue = Queue()
    wallet_thread = None
    save_thread = None
    save_queue = Queue()
    tx_thread = None
    tx_queue = Queue()
    spent_tx = []
    unspent_tx = []
    spent_tx_dict = {}
    unspent_tx_dict = {}
    # Other variables
    wallet_height = None
    calculated_balance = 0.0
    total_balance = 0.0
    unlocked_balance = 0.0
    temp_tx_amount = 0.0
    temp_tx_hash = ""
    temp_tx_paymentid = ""
    wallet_save_time = None
    donate_CMC_input_amount = ObjectProperty()

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        if not os.path.isdir(self.data_dir):
            os.makedirs(self.data_dir)
        self.daemon_server_textinput.text = daemon_URL
        if os.path.isfile(os.path.join(self.data_dir, 'CONFIG.file')):
            with open(os.path.join(self.data_dir, 'CONFIG.file'), 'r') as f:
                lines = f.readlines()
            try:
                self.wallet_name = lines[0].rstrip().split('=')[1].lstrip()
                self.daemon_server_textinput.text = lines[1].rstrip().split('=')[1].lstrip()
                self.daemon_thread = Thread(target=self.checkDaemonStatus,
                                            args=(self.daemon_queue, self.daemon_server_textinput.text))
                self.daemon_thread.daemon = True
                self.daemon_thread.start()
                Clock.schedule_once(self.initialPassword, 0.5)
            except:
                Clock.schedule_once(self.initialConfig, 0.5)
        else:
            Clock.schedule_once(self.initialConfig, 0.5)
        self.balance_thread = Thread(target=self.checkBalanceStatus, args=(self.balance_queue,))
        self.balance_thread.daemon = True
        self.balance_thread.start()
        self.tx_thread = Thread(target=self.checkTransactionsStatus, args=(self.tx_queue,))
        self.tx_thread.daemon = True
        self.tx_thread.start()
        Clock.schedule_interval(self.checkDaemon, 7)
        Clock.schedule_interval(self.checkBalance, 7)
        Clock.schedule_interval(self.checkTransactions, 12)
        Clock.schedule_interval(self.saveWallet, 180)
        self.ids.unspent_tx_list.bind(minimum_height=self.ids.unspent_tx_list.setter('height'))
        self.ids.spent_tx_list.bind(minimum_height=self.ids.spent_tx_list.setter('height'))

    def initialConfig(self, dt):
        ip = InitialPopup()
        ip.open()

    def initialPassword(self, dt):
        gp = PasswordPopup(self.wallet_name)
        gp.open()

    def checkDaemonStatus(self, daemon_queue, server):
        """Method to be threaded for checking bitmonerod status"""
        while True:
            height, reward, timesince, localtime = checkLastBlock(server + "/json_rpc")
            daemon_queue.put((height, reward, timesince, localtime))
            time.sleep(5)

    def checkDaemon(self, dt):
        """RPC call to check bitmonerod for blockchain info"""
        try:
            height, reward, timesince, localtime = self.daemon_queue.get_nowait()
            self.blockheight = int(height)
            self.blockheight_label.text = "[b][color=00ffff]{0}[/b][/color]".format(height)
            self.last_reward_label.text = "[b][color=00ffff]{0:.2f}[/b][/color] XMR".format(reward * 1e-12)
            self.last_block_time_label.text = "[b][color=00ffff]{0}[/b][/color]".format(localtime)
            self.time_since_last_label.text = "[b][color=00ffff]{0:.0f}[/b][/color] seconds".format(timesince)
            self.wallet_block_label.text = "[b][color=00ffff]{0}[/b][/color] of [b][color=00ffff]{1}[/b][/color]".format(
                    self.wallet_height, self.blockheight)
        except:
            self.blockheight_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No daemon connection")
            self.last_reward_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No daemon connection")
            self.last_block_time_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No daemon connection")
            self.time_since_last_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No daemon connection")
            self.wallet_block_label.text = "[b][color=ff0000]{0}[/b][/color] of [b][color=ff0000]{1}[/b][/color]".format(
                    self.wallet_height, "No daemon connection")

    def checkBalanceStatus(self, balance_queue):
        """Method to be threaded for checking balance status"""
        while True:
            balance, unlocked_balance = checkBalanceSimplewallet()
            balance_queue.put((balance, unlocked_balance))
            time.sleep(5)

    def checkBalance(self, dt):
        """RPC call to check bitmonerod for blockchain info"""
        try:
            balance, unlocked_balance = self.balance_queue.get_nowait()
            try:
                self.total_balance_label.text = "[b][color=00ffff]{0:.4f}[/b][/color] XMR".format(float(balance))
                self.unlocked_balance_label.text = "[b][color=00ffff]{0:.4f}[/b][/color] XMR".format(float(unlocked_balance))
                self.unlocked_balance, self.total_balance = float(unlocked_balance), float(balance)
            except ValueError:
                self.total_balance_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No wallet connection or syncing")
                self.unlocked_balance_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No wallet connection or syncing")
        except Empty:
            # print("empty")
            self.total_balance_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No wallet connection or syncing")
            self.unlocked_balance_label.text = "[b][color=ff0000]{0}[/b][/color]".format("No wallet connection or syncing")

    def checkTransactionsStatus(self, tx_queue):
        """Method to be threaded for checking balance status"""
        while True:
            unspent_txs, spent_txs = getTransfers()
            tx_queue.put((unspent_txs, spent_txs))
            time.sleep(10)

    def checkTransactions(self, dt):
        """RPC call to check bitmonerod for blockchain info"""
        try:
            unspent_txs, spent_txs = self.tx_queue.get_nowait()
            if len(unspent_txs) > len(self.unspent_tx) or len(spent_txs) > len(self.spent_tx):
                self.unspent_tx = unspent_txs
                self.spent_tx = spent_txs
                self.unspent_tx_dict = {}
                self.spent_tx_dict = {}
                self.ids.unspent_tx_list.clear_widgets()
                self.ids.spent_tx_list.clear_widgets()
                temp_balance = 0.0
                for idx, val in enumerate(self.unspent_tx):
                    self.unspent_tx_dict[idx] = Button(text="tx_id: {0} | amount: {1:.4f}".format(val[0], val[1]),
                               size_hint_y=None, height=15, font_size=9)
                    self.unspent_tx_dict[idx].bind(on_press=self._create_button_callback(val[0]))
                    self.ids.unspent_tx_list.add_widget(self.unspent_tx_dict[idx])
                    temp_balance += val[1]
                for idx, val in enumerate(self.spent_tx):
                    self.spent_tx_dict[idx] = Button(text="tx_id: {0} | amount: {1:.4f}".format(val[0], val[1]),
                               size_hint_y=None, height=15, font_size=9)
                    self.spent_tx_dict[idx].bind(on_press=self._create_button_callback(val[0]))
                    self.ids.spent_tx_list.add_widget(self.spent_tx_dict[idx])
                self.calculated_balance_label.text = "[b][color=00ffff]{0:.4f}[/b][/color] XMR".format(float(temp_balance))
        except Empty:
            pass

    def _create_button_callback(self, val):
        def callback(button):
            Clipboard.put(val)
        return callback

    def launchWallet(self, wallet_name, wallet_pw):
        self.wallet_name = wallet_name
        self.wallet_pw = wallet_pw
        wallet_dir = os.path.join(self.data_dir, "{0}_walletData".format(wallet_name.replace('.', '')))
        wallet_file = os.path.join(wallet_dir, wallet_name)
        address_file = os.path.join(wallet_dir, wallet_name+".address.txt")
        if not os.path.isfile(wallet_file):
            print("binary file not found, creating...")
            p = Popen(["simplewallet.exe", "--wallet-file", wallet_file, "--password", wallet_pw],
                                          stdin=PIPE,
                                          stdout=PIPE,
                                          stderr=STDOUT,
                                          bufsize=1)
            q = Queue()
            t = Thread(target=enqueue_output, args=(p, q))
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
            try:
                p.communicate(input="exit\r\n")
            except:
                pass
            time.sleep(2)
            if sys.platform == 'win32':
                try:
                    p.kill()
                    print("Simplewallet process killed")
                except:
                    print("Wallet process not running")
                try:
                    windows_task_killer(App.get_running_app().root.wallet_process.pid)
                except:
                    print("Nonetype error")
            if not os.path.isfile(address_file):
                with open(address_file, 'w') as f:
                    f.write(address)
                    self.address = address
        if os.path.isfile(address_file):
            with open(address_file, 'r') as f:
                self.address = f.read().rstrip()
        time.sleep(2)
        self.calculated_balance_label.text = "[b][color=00ffff]{0:.4f}[/b][/color] XMR".format(self.calculated_balance)
        self.wallet_process = Popen(["simplewallet", "--wallet-file", wallet_file, "--password", wallet_pw,
                                     "--daemon-address", self.daemon_server_textinput.text, "--rpc-bind-port", "19091"],
                                      stdout=PIPE,
                                      stderr=STDOUT,
                                      bufsize=1)
        self.wallet_thread = Thread(target=enqueue_output,
                                    args=(self.wallet_process.stdout, self.wallet_queue))
        self.wallet_thread.daemon = True  # thread dies with the program
        self.wallet_thread.start()
        self.wallet_account_label.text = "[b][color=00ffff]{0}[/b][/color]".format(wallet_name)
        self.wallet_address_label.text = "[b][color=00ffff][ref=Address]{0}\n[size=14]Click to copy[/b][/color][/size][/ref]".format(self.address)
        Clock.schedule_interval(self.readWalletQueue, 1e-3)

    def readWalletQueue(self, dt):
        wallet_dir = os.path.join(self.data_dir, "{0}_walletData".format(self.wallet_name.replace('.', '')))
        wallet_file = os.path.join(wallet_dir, self.wallet_name)
        try:
            new_line = self.wallet_queue.get_nowait()
            # print(new_line)
            if "Wallet initialize failed: failed to read file" in new_line:
                self.wallet_thread.join()
                self.wallet_error = True
                os.remove(wallet_file)
                Clock.schedule_once(self.initialPassword, 0.5)
            if "Wallet initialize failed: invalid password" in new_line:
                self.wallet_thread.join()
                self.incorrect_password = True
                Clock.schedule_once(self.initialPassword, 0.5)
            if "height:" in new_line:
                try:
                    self.wallet_height = new_line.split(", ")[1].split(": ")[1]
                    self.wallet_block_label.text = "[b][color=00ffff]{0}[/b][/color] of [b][color=00ffff]{1}[/b][/color]".format(
                        self.wallet_height, self.blockheight)
                except:
                    print("height: read failed")
            elif "height " in new_line:
                try:
                    self.wallet_height = new_line.split(", ")[1].split(" ")[1]
                    self.wallet_block_label.text = "[b][color=00ffff]{0}[/b][/color] of [b][color=00ffff]{1}[/b][/color]".format(
                        self.wallet_height, self.blockheight)
                except:
                    print("height read failed")
            elif "Refresh done," in new_line:
                # print("refresh done")
                split_line = new_line.split(',')
                self.total_balance = float(split_line[2].split(': ')[1])
                self.unlocked_balance = float(split_line[3].split(': ')[1])
                self.total_balance_label.text = "[b][color=00ffff]{0:.4f}[/b][/color] XMR".format(self.total_balance)
                self.unlocked_balance_label.text = "[b][color=00ffff]{0:.4f}[/b][/color] XMR".format(self.unlocked_balance)
        except Empty:
            pass

    def saveWallet(self, dt):
        try:
            save_thread = Thread(target=self.storeWallet)
            save_thread.daemon = True
            save_thread.start()
            save_thread.join()
        except:
            print("Save failed")

    def storeWallet(self):
        response = storeWallet()
        try:
            response = storeWallet()
            if "jsonrpc" in response:
                local_save_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                self.wallet_savetime_label.text = "Wallet saved @\n[b][color=00ffff]{0}[/b][/color]".format(local_save_time)
                print("Finished save thread")
            elif "Waiting for" in response:
                self.wallet_savetime_label.text = "[color=ff0000]Wallet save failed\nprobably syncing[/color]"
        except:
            print("Major save fail!")

    def selectAddress(self):
        """Copy address to clipboard when user clicks"""
        print('User clicked on ', self.address)
        Clipboard.put(self.address)

    def transferfunds(self, address=None, mixin=None, amount=None, paymentid=None):
        if not address:
            address = self.address_input_textinput.text
        if not mixin:
            mixin = self.mixin_input_textinput.text
        if not amount:
            amount = self.amount_input_textinput.text
        if not paymentid:
            paymentid = self.paymentid_input_textinput.text
        print(address, mixin, amount, paymentid)
        print(len(paymentid), hex_match(paymentid))
        """Initiate transfer of funds to new address"""
        address_error_content = Button(text="Address must be 95 characters long\nand start with a '4'.\nClick to start over.",
                                       halign="center")
        address_error_popup = Popup(title="Address error", content=address_error_content, size_hint=(0.75, 0.75))
        address_error_content.bind(on_press=address_error_popup.dismiss)
        mixin_error_content = Button(text="Mixin must be an integer between 0 and 99.\nClick to start over.",
                                     halign="center")
        mixin_error_popup = Popup(title="Mixin error", content=mixin_error_content, size_hint=(0.75, 0.75))
        mixin_error_content.bind(on_press=mixin_error_popup.dismiss)
        if self.unlocked_balance > 0.01:
            amount_error_content = Button(text="Amount must be a number between 0.01 and {0:.3f} XMR.\nClick to start over.".format(self.unlocked_balance),
                                          halign="center")
        else:
            amount_error_content = Button(text="Amount must be a number greater than 0.01 XMR.\nClick to start over.".format(self.unlocked_balance),
                                          halign="center")
        amount_error_popup = Popup(title="Amount error", content=amount_error_content, size_hint=(0.75, 0.75))
        amount_error_content.bind(on_press=amount_error_popup.dismiss)
        paymentid_error_content = Button(text="Payment ID must be 0 or 64 hex characters long.\nClick to start over.",
                                         halign="center")
        paymentid_error_popup = Popup(title="Payment ID error", content=paymentid_error_content, size_hint=(0.75, 0.75))
        paymentid_error_content.bind(on_press=paymentid_error_popup.dismiss)
        try:
            address = address
            if len(address) != 95 or address[0] != '4':
                address_error_popup.open()
                return
        except IndexError:
            address_error_popup.open()
            return
        try:
            if not mixin:
                mixin = 0
            mixin = int(mixin)
            if mixin == 1:
                mixin = 0
            print(mixin)
            if not 0 <= mixin < 100:
                mixin_error_popup.open()
                return
        except ValueError:
            mixin_error_popup.open()
            return
        try:
            amount = float(amount)
            if not 0.01 <= amount <= self.unlocked_balance:
                amount_error_popup.open()
                return
        except ValueError:
            amount_error_popup.open()
            return
        try:
            paymentid = paymentid
            if len(paymentid) not in (0, 64) or not hex_match(paymentid):
                paymentid_error_popup.open()
                return
        except ValueError:
            paymentid_error_popup.open()
            return
        tp = TransferPopup(amount, address, mixin, paymentid)
        tp.open()

    def donate_CMC(self):
        CMC_donate_popup = DonateCMC()
        CMC_donate_popup.open()

    def donate_core(self):
        core_donate_popup = DonateCore()
        core_donate_popup.open()

    def changeTabs(self):
        print(self.root_widget.orientation)
        if self.root_widget.orientation == "horizontal":
            self.root_widget.orientation = "vertical"
        else:
            self.root_widget.orientation = "horizontal"


class lightWalletApp(App):
    def build(self):
        root = RootWidget()
        return root


if __name__ == '__main__':
    Config.set('kivy', 'exit_on_escape', 0)
    Config.set('kivy', 'window_icon', "./lilicon.ico")
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    lightWalletApp().run()
    try:
        tx_file = os.path.join(App.get_running_app().root.data_dir,
                               "{0}_walletData".format(App.get_running_app().root.wallet_name.replace('.', '')), "tx.txt")
        with open(tx_file, 'w') as txs:
            txs.write("Unspent tx outputs:\n")
            for i in App.get_running_app().root.unspent_tx:
                txs.write("tx_id: {0} | amount: {1:.4f}\n".format(i[0], i[1]))
            txs.write("\nSpent tx outputs:\n")
            for i in App.get_running_app().root.spent_tx:
                txs.write("tx_id: {0} | amount: {1:.4f}\n".format(i[0], i[1]))
    except:
        print("Problem writing tx file")
    if sys.platform == 'win32':
        try:
            App.get_running_app().root.wallet_process.kill()
            print("Simplewallet process killed")
        except:
            print("Wallet process not running")
        try:
            windows_task_killer(App.get_running_app().root.wallet_process.pid)
        except:
            print("Nonetype error")
    # time.sleep(1.5)
    if os.path.isfile("./simplewallet.log"):
        try:
            os.remove("./simplewallet.log")
        except WindowsError:
            print("File in use, can not be deleted!")

