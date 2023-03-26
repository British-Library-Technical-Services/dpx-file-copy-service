import logging
from datetime import datetime
import os
import sys
import yaml
import tkinter as tk
from tkinter import filedialog
import glob
from hash_file_services import ChecksumCopyService
import shutil
import time


logTS = datetime.now().strftime('%Y%m%d_%H.%M_log.log')
current_loc = os.getcwd()
log = '{}/logs/{}'.format(current_loc, logTS)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(module)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler(log)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

drive_collections = {}
collections = []
missing = []
failed = []

print('''
-------------------------------------------------------
------|| Welcome to the DPX File Copy Service ||-------
-------------------------------------------------------
''')
time.sleep(1)


class DpxProcessing:
    def __init__(self):

        self.drive_data = '{}/data/WA2011.yml'.format(current_loc)
        self.src = None
        self.dst = None
        self.dpx = None
        self.dpx_files = None
        self.src_manifest = None
        self.dst_manifest = None
        self.copy_location = None
        self.safe_copy_location = None
        self.failed_copy_location = None

    def get_drive_data(self):
        with open(self.drive_data, 'r') as collection_list:
            data = yaml.load(collection_list, Loader=yaml.FullLoader)
            drive_collections.update(data)

    def set_dpx_files(self):
        for key, value in drive_collections.items():
            print('Insert {} and select the SOURCE location'.format(key))
            time.sleep(2)

            self.src = filedialog.askdirectory()
            src_dpx = [dir for dir in os.listdir(self.src)
                       if os.path.isdir(os.path.join(self.src, dir))]

            logger.info('{} set as SOURCE'.format(self.src))

            for f in value['directories']:
                if f in src_dpx:
                    collections.append(f)
                else:
                    missing.append(f)

            if len(missing) > 0:
                logger.warning('WARNING: {} NOT IN SOURCE LOCATION'.format(missing))
                print('Would you like to continue?')
                print('Press \'q\' to QUIT or press any other key to continue:')
                if input() == 'q':
                    sys.exit(0)
                    logger.info('User chose to quit')

                else:
                    logger.info('User chose to continue')

            print('Select copy DESTINATION')
            self.dst = filedialog.askdirectory()

        missing[:] = []

    def dpx_copying_service(self):
        for self.collection in collections:
            self.dpx = os.path.join(self.src, self.collection)
            self.dpx_files = sorted(glob.glob(self.dpx + '/*.dpx'))
            hash_manifest = '{}_dpx_hash_manifest.md5'.format(self.collection)
            self.src_manifest = os.path.join(self.dpx, hash_manifest)
            self.dst_manifest = os.path.join(self.dst, self.collection, hash_manifest)
            self.copy_location = os.path.join(self.dst, self.collection)

            print('\n', '-----| {} |-----'.format(self.collection))

            if os.path.exists(self.dst):
                try:
                    if not os.path.exists(self.copy_location):
                        os.mkdir(self.copy_location)
                    else:
                        logger.warning('{} EXISTS in DESTINATION'.format(self.copy_location))
                        # print('{} EXIST in DESTINATION'.format(self.collection))

                    if os.path.isfile(self.dst_manifest):
                        logger.warning('{} EXISTS in DESTINATION'.format(self.dst_manifest))
                        # print('{} EXISTS in DESTINATION'.format(self.dst_manifest))

                    else:
                        write_dst_manifest = open(self.dst_manifest, 'w')
                        write_dst_manifest.close()

                    if len(self.dpx_files) == 0:
                        print('NO DPX FILES FOUND, skipping')
                        logger.warning('{} NO DPX FILES found, skipping'.format(self.collection))
                    else:
                        if os.path.isfile(self.src_manifest):
                            logger.warning('{} EXISTS in SOURCE'.format(self.src_manifest))
                            # print('{} EXISTS in SOURCE'.format(self.src_manifest))

                        else:
                            write_src_manifest = open(self.src_manifest, 'w')
                            write_src_manifest.close()

                except Exception as e:
                    print(e)
                    logger.exception(e)

            count = len(self.dpx_files)
            i = 1

            for file in self.dpx_files:
                time.sleep(1)
                print('\r', 'Processing {} of {} dpx files'.format(i, count), end='', flush=True)
                i += 1

                if not os.path.isdir(file):

                    file_name_only = os.path.basename(file)
                    copied_file = os.path.join(self.copy_location, file_name_only)

                    ccs = ChecksumCopyService(file, file_name_only, self.src_manifest, self.dst_manifest, self.copy_location)
                    ccs.generate()
                    ccs.copy()
                    validation_check = ccs.verify()

                    self.safe_copy_location = os.path.join(self.dpx, '_copied')
                    self.failed_copy_location = os.path.join(self.dpx, '_failed')

                    try:
                        if os.path.isfile(copied_file) and validation_check:
                            if not os.path.exists(self.safe_copy_location):
                                os.mkdir(self.safe_copy_location)

                            shutil.move(file, os.path.join(self.safe_copy_location, file_name_only))
                            logger.info('SUCCESS: {}'.format(file_name_only))

                        elif not os.path.isfile(copied_file) or validation_check:
                            if not os.path.exists(self.failed_copy_location):
                                os.mkdir(self.failed_copy_location)

                            shutil.move(file, os.path.join(self.failed_copy_location, file_name_only))
                            logger.critical('FAILED: {}'.format(file_name_only))
                            failed.append(file)

                    except Exception as e:
                        print(e)
                        logger.exception(e)
                else:
                    pass

            if len(failed) > 0:
                print('\n*** {} files FAILED - see log for details ***'.format(len(failed)))

        collections[:] = []


dp = DpxProcessing()
dp.get_drive_data()
dp.set_dpx_files()
dp.dpx_copying_service()
input('\nCOMPLETE. Press any key to exit.')