import gridfs
import os
import pymongo


def main():
    db = pymongo.MongoClient(os.environ['CHANGE_STREAM_DB']).bigfiles
    file_name = "./20MB_file"
    with open(file_name, "rb") as file_data:
        data = file_data.read()

    fs = gridfs.GridFS(db)

    # store file
    a = fs.put(data, filename="20MB_file_python")
    print(a)
    b = fs.put(fs.get(a), filename="the_same_file")
    print(b)

    # retrieve
    doc = db.fs.files.find_one({'filename': "20MB_file_python"})
    res = fs.get(doc['_id']).read()
    download_location = "./20MB_file_python"
    with open(download_location, "wb") as output:
        output.write(res)

    # retrieve parts
    doc = db.fs.files.find_one({'filename': "20MB_file_python"})
    res = fs.get(doc['_id']).readchunk()
    print(res)


if __name__ == "__main__":
    main()
