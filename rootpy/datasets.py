import glob
from collections import namedtuple
import os
import sys
import re
from xml.dom import minidom

mcpattern = re.compile("^group(?P<year>[0-9]+).perf-tau.mc(?P<prodyear>[0-9]+)_(?P<energy>[0-9]+)TeV.(?P<run>[0-9]+).(?P<name>).(?P<tag>[^.]+).(?P<suffix>.+)$")
datapattern = re.compile("^group(?P<year>[0-9]+).(?P<group>[^.]+).(?P<run>[0-9]+).(?P<stream>[^.]+).(?P<tag>[^.]+).(?P<version>[0-9\-]+).D3PD(?:.(?P<edition>[0-9]+))?_StreamD3PD_Tau(?P<size>SMALL$|MEDIUM$)")

Dataset = namedtuple('Dataset', 'name datatype classtype treename weight files')

classes = {
    'BACKGROUND' :0,
    'SIGNAL'     :1
}

types = {
    'DATA' :0,
    'MC'   :1
}

data_periods = {
    'AB' :xrange(152166,155161),
    'C'  :xrange(155228,156683),
    'D'  :xrange(158045,159225),
    'E'  :xrange(160387,161949),
    'F'  :xrange(162347,162883),
    'G'  :xrange(165591,166384),
    'H'  :xrange(166466,166965)
}

if not os.environ.has_key('DATAROOT'):
    sys.exit("DATAROOT not defined!")
dataroot = os.environ['DATAROOT']

def get_sample(name, periods=None):

    base = os.path.join(dataroot,name)
    if not os.path.isdir(base):
        print "Sample %s not found at %s"%(name,base)
        return None
    metafile = os.path.join(base,'meta.xml')
    if not os.path.isfile(metafile):
        print "Metadata %s not found!"%metafile
        return None
    try:
        doc = minidom.parse(metafile)
        meta = doc.getElementsByTagName("meta")
        datatype = meta[0].getElementsByTagName("type")[0].childNodes[0].nodeValue.upper()
        classname = meta[0].getElementsByTagName("class")[0].childNodes[0].nodeValue.upper()
        weight = float(eval(str(meta[0].getElementsByTagName("weight")[0].childNodes[0].nodeValue)))
        treename = str(meta[0].getElementsByTagName("tree")[0].childNodes[0].nodeValue)
    except:
        print "Could not parse metadata!"
        return None 
    if not classes.has_key(classname):
        print "Class %s is not defined!"%classname
        if len(classes) > 0:
            print "Use one of these:"
            for key in classes.keys():
                print key
        else:
            print "No classes have been defined!"
        return None
    classtype = classes[classname]
    if not types.has_key(datatype):
        print "Datatype %s is not defined!"%datatype
        if len(types) > 0:
            print "Use one of these:"
            for key in types.keys():
                print key
        else:
            print "No datatypes have been defined!"
    datatype = types[datatype]
    dirs = glob.glob(os.path.join(base,'*'))
    actualdirs = []
    for dir in dirs:
        if os.path.isdir(dir):
            actualdirs.append(dir)
    files = []
    samplename = name
    if datatype == types['DATA']:
        # check for duplicate runs and take last edition
        runs = {}
        for dir in actualdirs:
            datasetname = os.path.basename(dir)
            match = re.match(datapattern,datasetname)
            if not match:
                print "Warning: directory %s is not a valid dataset name!"%datasetname
            else:
                runnumber = int(match.group('run'))
                if periods != None:
                    isinperiod = False
                    for period in periods:
                        if not data_periods.has_key(period):
                            print "Period %s is not defined!"%period
                            return None
                        if runnumber in data_periods[period]:
                            isinperiod = True
                            break
                    if not isinperiod:
                        continue
                edition = 0
                if match.group('edition'):
                    edition = int(match.group('edition'))
                if runs.has_key(runnumber):
                    print "Warning: multiple editions of dataset %s exist!"%datasetname
                    if edition > runs[runnumber]['edition']:
                        runs[runnumber] = {'edition':edition, 'dir':dir}
                else:
                    runs[runnumber] = {'edition':edition, 'dir':dir}
        for key,value in runs.items():
            files += glob.glob(os.path.join(value['dir'],'*root*'))
        if periods:
            samplename += "_%s"%("".join(periods))
    else:
        for dir in actualdirs:
            files += glob.glob(os.path.join(dir,'*root*'))
    return Dataset(samplename,datatype,classtype,treename,weight,files)