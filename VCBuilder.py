import urllib
import urllib2
from xml.dom.minidom import parseString

class VCBuilder:
	def __init__(self, username, password, evServer):
	  self.targetServer = evServer
	  self.password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
	  self.password_mgr.add_password(None, evServer, username, password)
	  self.handler = urllib2.HTTPBasicAuthHandler(self.password_mgr)
	  self.opener = urllib2.build_opener(self.handler)
	  urllib2.install_opener(self.opener)

	def GetPrimaryArchive(self):
  	  print('Fetching Accessible archives...')
  	  url = self.targetServer + 'ListArchives.aspx'
  	  req = urllib2.Request(url)
  	  f = urllib2.urlopen(req)
  	  data = f.read()
  	  f.close()

  	  dom = parseString(data)
  	  Archive_node = dom.getElementsByTagName('Archive')[0]
  	  archiveName = Archive_node.getAttribute('ArchiveName')
  	  vaultID = Archive_node.getAttribute('VaultEntryId')

  	  print('\tFound archive: ' + archiveName)
  	  return {'ArchiveName' : archiveName, 'VaultID' : vaultID}

	def GetVaultInfo(self, archiveID):
	  print('Fetching Vault information for Archive ' + archiveID + '...')

  	  values = {'ArchiveId' : archiveID,
     	     	'action' : 'GetVaultInformation'}

  	  data = urllib.urlencode(values)
  	  url = self.targetServer + 'GetVaultInformation.aspx'
  	  req = urllib2.Request(url, data)
  	  f = urllib2.urlopen(req)
  	  data = f.read()
  	  f.close()

  	  dom = parseString(data)
  	  CONTENTCACHE_node = dom.getElementsByTagName('CONTENTCACHE')[0]

  	  maxSNUM = CONTENTCACHE_node.getAttribute('MaxSNUM')
  	  itemCount = CONTENTCACHE_node.getAttribute('ItemCount')
  	  startDate = CONTENTCACHE_node.getAttribute('StartDate')
  	  endDate = CONTENTCACHE_node.getAttribute('EndDate')

	  print('Vault Information for archive (' + archiveID + ')')
  	  print('\tMax SNUM: ' + maxSNUM)
  	  print('\tItem Count: ' + itemCount + ' item/s')
  	  print('\tStart date: ' + startDate)
  	  print('\tEnd Date: ' + endDate)

  	  return {'StartDate' : startDate,
  	  		  'EndDate' : endDate,
  	  		  'MaxSNUM' : maxSNUM,
  	  		  'Count' : itemCount
  	  		 }

if __name__ == "__main__":

	vcBuilder = VCBuilder('USER', 'PASSWORD', 'http://SERVER_ADDRESS/EnterpriseVault/')
	
	archiveList = vcBuilder.GetPrimaryArchive()
	vaultInfo = vcBuilder.GetVaultInfo(archiveList['VaultID'])

