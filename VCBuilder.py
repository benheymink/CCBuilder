import urllib
import urllib2
import time
import sys
from xml.dom.minidom import parseString

class VCBuilder:
  def __init__(self, username, password, evServer):
    self.targetServer = evServer
    self.password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    self.password_mgr.add_password(None, evServer, username, password)
    self.handler = urllib2.HTTPBasicAuthHandler(self.password_mgr)
    self.opener = urllib2.build_opener(self.handler)
    urllib2.install_opener(self.opener)

  def GetFirstAccessibleArchiveInList(self):
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

  def BuildAPST(self, archiveId, vaultInfo, startSeqNum):
    print('Starting build phase')

    startDate = vaultInfo['StartDate']
    endDate = vaultInfo['EndDate']

    values = {'ArchiveId' : archiveId, 'StartDate' : startDate[:-9], 'EndDate' : endDate[:-9], 'MaxDbSize' : '512000', 'DbId' : '1', 'LastSnum' : startSeqNum, 'DeleteJobIds' : ''}

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

  def WaitForJobCompletion(self, dbId):
    print('Waiting for job to complete...')
    
    values = {'Id' : dbId, 'TestCounter' : '1'}
    data = urllib.urlencode(values)
    url = self.targetServer + 'HasJobBuiltYet.aspx'
    req = urllib2.Request(url, data)

    while (True):
        print('')
        print('Waiting for build to finish on the server (this will take a while)...')
        f = urllib2.urlopen(req)
        data = f.read()
        f.close()

        dom = parseString(data)

        if len(dom.getElementsByTagName('JOBCOMPLETED')) != 1:
            time.sleep(120)
            continue            

        JOBCOMPLETED_node = dom.getElementsByTagName('JOBCOMPLETED')[0]

        jobID = JOBCOMPLETED_node.getAttribute('Id')
        moreToCome = JOBCOMPLETED_node.getAttribute('MoreToCome')
        lastSnum = JOBCOMPLETED_node.getAttribute('LastSnum')
        size = JOBCOMPLETED_node.getAttribute('Size')
        cSize = JOBCOMPLETED_node.getAttribute('CSize')
        itemCount = JOBCOMPLETED_node.getAttribute('ItemCount')
        skipped = JOBCOMPLETED_node.getAttribute('Skipped')

        print('\tBuild completed, more to come: ' + moreToCome)
        print('')
        return {'ID' : jobID, 'MORE' : moreToCome, 'LASTSNUM' : lastSnum, 'ITEMCOUNT' : itemCount}


  def DownloadDBFile(self, jobID, filename):
    print('Downloading file... (' + jobID + ')')
    url = self.targetServer + 'DownloadContent.aspx?JobId=' + jobID
    req = urllib2.Request(url)

    file_name = 'C:\\PSTS\\File' + str(filename) + '.pst'
    response = urllib2.urlopen(url)
    self.chunk_read(file_name, response, report_hook=self.chunk_report)

    print('File downloaded! (Saved to: ' + file_name + ')')

  def chunk_report(self, bytes_so_far, chunk_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent*100, 2)
    sys.stdout.write("\r%2d%%" % percent)
    sys.stdout.flush()

    if bytes_so_far >= total_size:
       sys.stdout.write('\n')

  def chunk_read(self, file_name, response, chunk_size=8192, report_hook=None):
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0

    PSTFile = open(file_name, 'wb')

    while 1:
        chunk = response.read(chunk_size)
        bytes_so_far += len(chunk)

        if not chunk:
            break
    
        PSTFile.write(chunk)
        

        if report_hook:
            report_hook(bytes_so_far, chunk_size, total_size)

    PSTFile.close()
    return bytes_so_far

  def DeleteFileOnServer(self, jobID):
    print('Deleting file on server (' + jobID + ')...')

    values = {'DeleteJobIds' : jobID + ' ', 'action' : 'DeleteJob'}

    data = urllib.urlencode(values)
    url = self.targetServer + 'DeleteJob.aspx'
    req = urllib2.Request(url, data)
    f = urllib2.urlopen(req)
    f.close()
    #fire and forget!
    print('Done!')

if __name__ == "__main__":

  vcBuilder = VCBuilder('USER_NAME', 'PASSWORD', 'http://EV_SERVER/EnterpriseVault/')
  
  archiveList = vcBuilder.GetFirstAccessibleArchiveInList()
  
  vaultInfo = vcBuilder.GetVaultInfo(archiveList['VaultID'])
  
  seqNum = vaultInfo['MaxSNUM']
  filename = 1

  moreToCome = '1'
  while (moreToCome == '1'):
      dbId = vcBuilder.BuildAPST(archiveList['VaultID'], vaultInfo, seqNum)
      jobInfo = vcBuilder.WaitForJobCompletion(dbId)
      vcBuilder.DownloadDBFile(jobInfo['ID'], filename)
      # Be good and clean up the file on the server!
      vcBuilder.DeleteFileOnServer(jobInfo['ID'])
      moreToCome = jobInfo['MORE']

      if (moreToCome == '1'):
          print('More to download, adjusting sequence numbers to download more')
          seqNum = jobInfo['LASTSNUM']
          filename += 1
          continue

  print('All done.')

