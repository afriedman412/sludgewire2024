from src.house.sql import FileTable

if __name__ == "__main__":
    f = FileTable()
    print('new')
    f.get_new_file_list()
    print('old')
    f.get_old_file_list()
    print('compare')
    f.compare_file_list()
    print('update')
    f.update_files()
    f.upload_new_data()
    print('texting')
    f.send_text()
