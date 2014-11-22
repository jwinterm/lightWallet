# lightWallet Kivy GUI
This is a GUI frontend that runs on top of bitmonerod and simplewallet (in RPC mode). It is designed to work with a remote bitmonerod node, so that it can function as a lightweight wallet for most users. **This program is an early beta version, and although I don't think there is really any way to screw up your wallet, please exercise some modicum of caution.**

## Installation
### Windows, Linux, and Mac
The requirements for running the program are: Python 2.7, Kivy 1.8, and pygame 1.9.1. If you have these requirements, then you just need to add your binary (simplewallet.exe)  and optionally wallet files to your cryptonoteRPCwalletGUI folder, or unzip the cryptonoteRPCwalletGUI contents into the folder where you currently have your binaries and wallet files. For the time being they have to be in the same local directory.

Currently there are no binaries available, but the plan is to compile an exe for Windows, andfrom there it should be easy to create binaries for linux. 

## Running
It should be OK to launch the program with an instance of bitmonerod and/or simplewallet running. 

On the initial run, it will prompt you to create a new wallet or to import one by typing/copying in the path of the keys file. This will create a folder in the local directory where the new/imported wallet data is stored, and a file called CONFIG.file that let's lightWallet know which account is currently the default one being used.

## Future Work
There are several features I'd like to implement, the most important of which is probably tab or file keeping a record of all incoming and outgoing transactions. This is a really key feature that should probably be a part of any wallet, but I'm still having some trouble with the gui here, so it is delayed for the time being. 

Another thing I want to change is using argparse rather than argv to parse command line arguments. This should make the program more robust (less crashy) and offer the user additional help at the command line. I probably want to clean up the interface and prettify it a bit more too. I'm open to suggestions too, so please open an issue or email me if you have any ideas, complaints, etc.