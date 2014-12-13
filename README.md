# lightWallet Kivy GUI
This is a GUI frontend that runs on top of bitmonerod and simplewallet (in RPC mode). It is designed to work with a remote bitmonerod node, so that it can function as a lightweight wallet for most users. By default it uses hegemoOn's open node at http://xmr1.coolmining.club:5012, but you can change the node it uses in the CONFIG.file stored in the My Documents/lightWallet directory; a local bitmonerod instance with http://localhost:18081 or Atrides recently launched an open node at http://node.moneroclub.com:8880. 

**This program is an alpha version, and although I don't think there is really any way to screw up your wallet, please exercise some modicum of caution.**

## Installation
### Windows, Linux, and Mac
The requirements for running the program from the source files are: Python 2.7, Kivy 1.8, and pygame 1.9.1. The program is also only intended for windows at the moment; it may be semi-functional on linux or mac, but I don't think it will work properly. If you have these requirements, then you just need to add your binary, simplewallet.exe(currently designed to work only with the latest tagged release),  and optionally wallet files to your cryptonoteRPCwalletGUI folder, or unzip the cryptonoteRPCwalletGUI contents into the folder where you currently have your binaries and wallet files. For the time being they have to be in the same local directory.

If you're using the binary (v0.0.1), there are no requirements other than an x64 Windows computer. 

## Running
It should be OK to launch the program with an instance of bitmonerod and/or simplewallet running. 

On the initial run, it will prompt you to create a new wallet or to import one by typing/copying in the path of the keys file. This will create a folder in the local directory where the new/imported wallet data is stored, and a file called CONFIG.file that let's lightWallet know which account is currently the default one being used. If you would like to create/import a new wallet, you can simply delete CONFIG.file and it will run the initial config prompt again (this won't affect any wallet folders already in the lightWallet directory).

## Known issues
The transaction history and calculated balance features are not fully working yet. This is something I plan to address, but since the wallet itself works (and simplewallet itself doesn't really implement a transaction history), and you can always see your balances with the total and unlocked balance readings, I decided to go ahead and release this alpha version, and will work on this in the future.

If you manage to crash the program, you will probably get an instance of simplewallet.exe hanging around, so to get rid of it you will need to go into the task manager processes tab and end the simplewallet process, or restart your computer.

The import keys does not work with deprecated wallets (wallets with no electrum seed) at the moment. This is an issue with simplewallet that will be addressed in the next release.

## Future Work
There are several features I'd like to implement, the most important of which is probably tab for an address book, where you can store addresses (and payment ids) that are each a button, and when you click the button it autofills everything on the transfer tab. Of course I'm working on the record keeping of all incoming and outgoing transactions and the calculated balance which is derived from them. This is a really key feature that should probably be a part of any wallet, but the wallet is still functional at the moment, and the transaction history is quasi-functional.

I'd like to figure out why the stdout output of simplewallet.exe lags sometimes, and it doesn't look like the wallet is quite synced up; this doesn't affect anything except making the wallet appear like it is a few blocks behind the daemon. Another thing I want to change is using argparse rather than argv to parse command line arguments. 

I want to clean up the interface and prettify it a bit more too. I'm open to suggestions, so please open an issue or email me if you have any ideas, complaints, etc.