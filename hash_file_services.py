import logging
import os
import hashlib
import shutil

logger = logging.getLogger('__main__.' + __name__)


class ChecksumCopyService:
    def __init__(self, file, file_name_only, src_manifest, dst_manifest, copy_location):

        self.hash_verified = False
        self.file = file
        self.file_name_only = file_name_only
        self.src_manifest = src_manifest
        self.dst_manifest = dst_manifest
        self.copy_location = copy_location

    def generate(self):

        with open(self.file, 'rb') as f:
            md5 = hashlib.md5()
            while buffer := f.read(8192):
                md5.update(buffer)

            hash = md5.hexdigest()
            hash_write = '{} *{}'.format(hash, self.file_name_only)

        with open(self.src_manifest, 'r') as register:
            if hash_write in register.read():
                logger.warning('MD5 hash for {} EXISTS in SOURCE manifest'.format(self.file_name_only))
            else:
                with open(self.src_manifest, 'a') as register:
                    register.write(hash_write + '\n')
                    logger.info('GENERATED: {} hash for {}'.format(hash, self.file_name_only))

        with open(self.dst_manifest, 'r') as register:
            if hash_write in register.read():
                logger.warning('MD5 hash for {} EXISTS in DESTINATION register'.format(self.file_name_only))
            else:
                with open(self.dst_manifest, 'a') as register:
                    register.write(hash_write + '\n')

    def copy(self):

        file_check = os.path.join(self.copy_location, self.file_name_only)
        if os.path.isfile(file_check):
            logger.warning('{} EXISTS in DESTINATION'.format(self.file_name_only))
        else:
            if os.path.exists(self.copy_location):
                try:
                    shutil.copy2(self.file, self.copy_location)
                    if os.path.isfile(file_check):
                        logger.info('COPIED: {} to {}'.format(self.file_name_only, self.copy_location))
                except Exception as e:
                    print(e)
                    logger.exception(e)
            else:
                pass

    def verify(self):

        file_verification = os.path.join(self.copy_location, self.file_name_only)
        if os.path.exists(self.copy_location):
            try:
                with open(self.dst_manifest, 'r') as verification_check:
                    for line in verification_check:
                        line_name = line[34:].strip()
                        if line_name == self.file_name_only:
                            line_hash = line[:32]
                            with open(file_verification, 'rb') as f:
                                md5 = hashlib.md5()
                                while buffer := f.read(8192):
                                    md5.update(buffer)
                                    file_hash = md5.hexdigest()

                                if file_hash == line_hash:
                                    logger.info('VERIFIED: {} hash for {}'.format(file_hash, self.file_name_only))

                                    self.hash_verified = True
                                    return self.hash_verified
                                else:
                                    logger.critical('***FAILED: {} did not verify***'.format(self.file_name_only))

                                    return self.hash_verified

            except Exception as e:
                print(e)
                logger.exception(e)
        else:
            pass
