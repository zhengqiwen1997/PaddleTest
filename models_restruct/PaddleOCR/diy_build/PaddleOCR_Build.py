# encoding: utf-8
"""
自定义环境准备
"""
import os
import sys
import time
import logging
import tarfile
import argparse
import subprocess
import platform
import numpy as np
import yaml
import wget
from Model_Build import Model_Build

logger = logging.getLogger("ce")


class PaddleOCR_Build(Model_Build):
    """
    自定义环境准备
    """

    def __init__(self, args):
        """
        初始化变量
        """
        self.paddle_whl = args.paddle_whl
        self.get_repo = args.get_repo
        self.branch = args.branch
        self.system = args.system
        self.set_cuda = args.set_cuda
        self.dataset_org = args.dataset_org
        self.dataset_target = args.dataset_target

        self.REPO_PATH = os.path.join(os.getcwd(), args.reponame)  # 所有和yaml相关的变量与此拼接
        self.reponame = args.reponame
        self.models_list = args.models_list
        self.models_file = args.models_file
        self.test_model_list = []
        if str(self.models_list) != "None":
            for line in self.models_list.split(","):
                if ".yaml" or ".yml" in line:
                    self.test_model_list.append(line.strip().replace("^", "/"))
                    print("self.test_model_list:{}".format(self.test_model_list))
        elif str(self.models_file) != "None":  # 获取要执行的yaml文件列表
            for file_name in self.models_file.split(","):
                for line in open(file_name):
                    if ".yaml" or ".yml" in line:
                        self.test_model_list.append(line.strip().replace("^", "/"))
        else:
            for file_name in os.listdir("cases"):
                if ".yaml" or ".yml" in file_name:
                    self.test_model_list.append(file_name.strip().replace("^", "/"))

    def build_dataset(self):
        """
        make datalink
        """
        if os.path.exists(self.reponame):
            path_now = os.getcwd()
            os.chdir(self.reponame)

            sysstr = platform.system()
            if sysstr == "Linux":
                src_path = "/ssd2/ce_data/PaddleOCR"
            elif sysstr == "Windows":
                src_path = "F:\\PaddleOCR"
                os.system("mklink /d train_data F:\\PaddleOCR\\train_data")
                os.system("mklink /d pretrain_models F:\\PaddleOCR\\pretrain_models")
            elif sysstr == "Darwin":
                src_path = "/Users/paddle/PaddleTest/ce_data/PaddleOCR"

            # dataset link
            # train_data_path = os.path.join(src_path, "train_data")
            # pretrain_models_path = os.path.join(src_path, "pretrain_models")

            # if not os.path.exists(train_data_path):
            #    os.makedirs(train_data_path)
            # if not os.path.exists(pretrain_models_path):
            #    os.makedirs(pretrain_models_path)
            if sysstr != "Windows":
                if not os.path.exists("train_data"):
                    os.symlink(os.path.join(src_path, "train_data"), "train_data")
                if not os.path.exists("pretrain_models"):
                    os.symlink(os.path.join(src_path, "pretrain_models"), "pretrain_models")

                # dataset
                if not os.path.exists("train_data/ctw1500"):
                    self.download_data("https://paddle-qa.bj.bcebos.com/PaddleOCR/train_data/ctw1500.tar", "train_data")

                if not os.path.exists("train_data/icdar2015"):
                    self.download_data(
                        "https://paddle-qa.bj.bcebos.com/PaddleOCR/train_data/icdar2015.tar", "train_data"
                    )
                if not os.path.exists("train_data/data_lmdb_release"):
                    self.download_data(
                        "https://paddle-qa.bj.bcebos.com/PaddleOCR/train_data/data_lmdb_release.tar", "train_data"
                    )
            # configs/rec/rec_resnet_stn_bilstm_att.yml
            # os.system("python -m pip install fasttext")
            # if not os.path.exists("cc.en.300.bin"):
            #    self.download_data(
            #        "https://paddle-qa.bj.bcebos.com/PaddleOCR/pretrain_models/cc.en.300.bin.tar", os.getcwd()
            #    )

            # kie requirements
            os.system("python -m pip install -r ppstructure/kie/requirements.txt")

            for filename in self.test_model_list:
                print("filename:{}".format(filename))
                if "rec" in filename:
                    if sysstr == "Darwin":
                        cmd = "sed -i '' 's!data_lmdb_release/training!data_lmdb_release/validation!g' %s" % filename
                    else:
                        cmd = "sed -i s!data_lmdb_release/training!data_lmdb_release/validation!g %s" % filename

                    subprocess.getstatusoutput(cmd)
            os.chdir(path_now)
            print("build dataset!")

    def download_data(self, data_link, destination):
        """
        下载数据集
        """
        tar_name = data_link.split("/")[-1]
        logger.info("start download {}".format(tar_name))
        wget.download(data_link, destination)
        logger.info("start tar extract {}".format(tar_name))
        tf = tarfile.open(os.path.join(destination, tar_name))
        tf.extractall(destination)
        time.sleep(10)
        os.remove(os.path.join(destination, tar_name))

    def build_env(self):
        """
        使用父类实现好的能力
        """
        super(PaddleOCR_Build, self).build_env()
        ret = 0
        ret = self.build_dataset()
        if ret:
            logger.info("build env dataset failed")
            return ret
        return ret
