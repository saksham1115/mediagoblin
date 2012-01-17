# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import Image
import os

from mediagoblin import mg_globals as mgg

from mediagoblin.processing import BadMediaFail, \
    create_pub_filepath, THUMB_SIZE, MEDIUM_SIZE

################################
# Media processing initial steps
################################


def process_image(entry):
    """
    Code to process an image
    """
    workbench = mgg.workbench_manager.create_workbench()
    # Conversions subdirectory to avoid collisions
    conversions_subdir = os.path.join(
        workbench.dir, 'conversions')
    os.mkdir(conversions_subdir)

    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    filename_bits = os.path.splitext(queued_filename)
    basename = os.path.split(filename_bits[0])[1]
    extension = filename_bits[1].lower()

    try:
        thumb = Image.open(queued_filename)
    except IOError:
        raise BadMediaFail()

    thumb.thumbnail(THUMB_SIZE, Image.ANTIALIAS)

    # Copy the thumb to the conversion subdir, then remotely.
    thumb_filename = 'thumbnail' + extension
    thumb_filepath = create_pub_filepath(entry, thumb_filename)
    tmp_thumb_filename = os.path.join(
        conversions_subdir, thumb_filename)
    with file(tmp_thumb_filename, 'w') as thumb_file:
        thumb.save(thumb_file)
    mgg.public_store.copy_local_to_storage(
        tmp_thumb_filename, thumb_filepath)

    # If the size of the original file exceeds the specified size of a `medium`
    # file, a `medium.jpg` files is created and later associated with the media
    # entry.
    medium = Image.open(queued_filename)
    medium_processed = False

    if medium.size[0] > MEDIUM_SIZE[0] or medium.size[1] > MEDIUM_SIZE[1]:
        medium.thumbnail(MEDIUM_SIZE, Image.ANTIALIAS)

        medium_filename = 'medium' + extension
        medium_filepath = create_pub_filepath(entry, medium_filename)
        tmp_medium_filename = os.path.join(
            conversions_subdir, medium_filename)

        with file(tmp_medium_filename, 'w') as medium_file:
            medium.save(medium_file)

        mgg.public_store.copy_local_to_storage(
            tmp_medium_filename, medium_filepath)

        medium_processed = True

    # we have to re-read because unlike PIL, not everything reads
    # things in string representation :)
    queued_file = file(queued_filename, 'rb')

    with queued_file:
        #create_pub_filepath(entry, queued_filepath[-1])
        original_filepath = create_pub_filepath(entry, basename + extension) 

        with mgg.public_store.get_file(original_filepath, 'wb') \
            as original_file:
            original_file.write(queued_file.read())

    mgg.queue_store.delete_file(queued_filepath)
    entry.queued_media_file = []
    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict['thumb'] = thumb_filepath
    media_files_dict['original'] = original_filepath
    if medium_processed:
        media_files_dict['medium'] = medium_filepath

    # clean up workbench
    workbench.destroy_self()
