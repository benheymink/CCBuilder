CCBuilder
=========

Python Script to run against an Enterprise Vault server to build a user's Content Cache locally.

This script can be paired with a custom HTTP Module to intercept calls to GetSlotWithServer.aspx and HasJobBuiltYet.aspx
to ensure no work is done on the server.