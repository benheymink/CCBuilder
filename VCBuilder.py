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

    values = {'ArchiveId' : archiveID, 'action' : 'GetVaultInformation'}

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

  def BuildAPST(self, archiveId, vaultInfo):
    print('Starting build phase')

    #Abuse the fact that we can specify any date range to the server
    #action=GetSlotWithServer&ArchiveId=13F4B32526C97F7439F96D538D6506EC21110000ECTO1-EVSVR-VM.gpk.rnd.veritas.com&StartDate=2012-04-01&EndDate=2012-06-30&MaxDbSize=512000&DbId=1&LastSnum=80&DeleteJobIds=
    values = {'ArchiveId' : archiveId, 'StartDate' : '2010-04-01', 'EndDate' : '2010-06-30', 'MaxDbSize' : '512000', 'DbId' : '1', 'LastSnum' : '0', 'DeleteJobIds' : ''}

    data = urllib.urlencode(values)
    url = self.targetServer + 'GetSlotWithServer.aspx'
    req = urllib2.Request(url, data)
    f = urllib2.urlopen(req)
    data = f.read()
    f.close()

    dom = parseString(data)
    CONTENTCACHE_node = dom.getElementsByTagName('CONTENTCACHE')[0]

    dbID = CONTENTCACHE_node.getAttribute('Id')
    print('Build Started, ID: ' + dbID)
    return dbID

  def GetJobID(dbId):
    print('Waiting for job to complete...')

    values = {'Id' : dbId, 'TestCounter' : '1'}

    data = urllib.urlencode(values)
    url = self.targetServer + 'HasJobBuiltYet.aspx'
    req = urllib2.Request(url, data)
    f = urllib2.urlopen(req)
    data = f.read()
    f.close()

    dom = parseString(data)
    JOBCOMPLETED_node = dom.getElementsByTagName('JOBCOMPLETED ')[0]

    jobID = JOBCOMPLETED_node.getAttribute('Id')
    moreToCome = JOBCOMPLETED_node.getAttribute('MoreToCome')
    lastSnum = JOBCOMPLETED_node.getAttribute('LastSnum')
    size = JOBCOMPLETED_node.getAttribute('Size')
    cSize = JOBCOMPLETED_node.getAttribute('CSize')
    itemCount = JOBCOMPLETED_node.getAttribute('ItemCount')
    skipped = JOBCOMPLETED_node.getAttribute('Skipped')


  def DownloadDBFile(self, jobID):
    print('Downloading file ' + jobID)

if __name__ == "__main__":

  vcBuilder = VCBuilder('USER', 'PASSWORD', 'http://EV_SERVER_NAME/EnterpriseVault/')
  
  archiveList = vcBuilder.GetPrimaryArchive()
  
  vaultInfo = vcBuilder.GetVaultInfo(archiveList['VaultID'])
  
  dbId = vcBuilder.BuildAPST(archiveList['VaultID'], vaultInfo)

  jobID = vcBuilder.GetJobID(dbId)

  vcBuilder.DownloadDBFile(jobID)