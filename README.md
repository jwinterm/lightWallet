# lightWallet Kivy GUI
This is a GUI frontend that runs on top of bitmonerod and simplewallet (in RPC mode). It is designed to work with a remote bitmonerod node, so that it can function as a lightweight wallet for most users. By default it uses Atrides open node at http://node.moneroclub.com:8880, but you can change the node it uses in the CONFIG.file stored in the My Documents/lightWallet directory; to use a local bitmonerod instance set it as http://localhost:18081. 

**This program is an alpha version, and although I don't think there is really any way to screw up your wallet, please exercise some modicum of caution.**

## Installation
### Windows, Linux, and Mac
The requirements for running the program from the source files are: Python 2.7, Kivy 1.8, and pygame 1.9.1. The program is also only intended for windows at the moment; it may be semi-functional on linux or mac, but I don't think it will work properly. If you have these requirements, then you just need to add your binary, simplewallet.exe(currently designed to work only with the latest tagged release),  and optionally wallet files to your cryptonoteRPCwalletGUI folder, or unzip the cryptonoteRPCwalletGUI contents into the folder where you currently have your binaries and wallet files. For the time being they have to be in the same local directory.

If you're using the binary (v0.0.3), there are no requirements other than an x64 Windows computer. 

## Running
It should be OK to launch the program with an instance of bitmonerod and/or simplewallet running. 

On the initial run, it will prompt you to create a new wallet or to import one by typing/copying in the path of the keys file. This will create a folder in the your user's My Documents directory in a folder called lightWallet (typically C:\Users\yourUser\Documents\lightWallet) where the new/imported wallet data is stored, and a file called CONFIG.file that let's lightWallet know which account is currently the default one being used. If you would like to create/import a new wallet, you can simply delete CONFIG.file and it will run the initial config prompt again (this won't affect any wallet folders already in the lightWallet directory).

## Known issues
If you manage to crash the program, you will probably get an instance of simplewallet.exe hanging around, so to get rid of it you will need to go into the task manager processes tab and end the simplewallet process, or restart your computer.

The import keys does not work with deprecated wallets (wallets with no electrum seed) at the moment. This is an issue with simplewallet that will be addressed in the next release of simplewallet.

## Future Work
There are several features I'd like to implement, the most important of which is probably a tab for an address book, where you can store addresses (and payment ids) that are each a button, and when you click the button it autofills everything on the transfer tab. 

I'd like to figure out why the stdout output of simplewallet.exe lags sometimes, and it doesn't look like the wallet is quite synced up; this doesn't affect anything except making the wallet appear like it is a few blocks behind the daemon or vice-versa. Another thing I want to change is using argparse rather than argv to parse command line arguments. 

I want to clean up the interface and prettify it a bit more too. I'm open to suggestions, so please open an issue or email me if you have any ideas, complaints, etc.