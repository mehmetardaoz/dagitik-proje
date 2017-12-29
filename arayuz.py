# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'arayuz.ui'
#
# Created by: PyQt5 UI code generator 5.5
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(822, 657)
        self.kullanici_list = QtWidgets.QListWidget(Form)
        self.kullanici_list.setGeometry(QtCore.QRect(450, 100, 341, 221))
        self.kullanici_list.setObjectName("kullanici_list")
        self.pushButton_connect = QtWidgets.QPushButton(Form)
        self.pushButton_connect.setGeometry(QtCore.QRect(550, 50, 151, 31))
        self.pushButton_connect.setObjectName("pushButton_connect")
        self.lineEdit_ip = QtWidgets.QLineEdit(Form)
        self.lineEdit_ip.setGeometry(QtCore.QRect(100, 50, 211, 31))
        self.lineEdit_ip.setObjectName("lineEdit_ip")
        self.lineEdit_port = QtWidgets.QLineEdit(Form)
        self.lineEdit_port.setGeometry(QtCore.QRect(330, 50, 201, 31))
        self.lineEdit_port.setObjectName("lineEdit_port")
        self.lineEdit_dosya_ismi = QtWidgets.QLineEdit(Form)
        self.lineEdit_dosya_ismi.setGeometry(QtCore.QRect(40, 130, 191, 41))
        self.lineEdit_dosya_ismi.setObjectName("lineEdit_dosya_ismi")
        self.pushButton_dosya_ara = QtWidgets.QPushButton(Form)
        self.pushButton_dosya_ara.setGeometry(QtCore.QRect(250, 140, 141, 31))
        self.pushButton_dosya_ara.setObjectName("pushButton_dosya_ara")
        self.dosya_list = QtWidgets.QListWidget(Form)
        self.dosya_list.setGeometry(QtCore.QRect(30, 200, 401, 281))
        self.dosya_list.setObjectName("dosya_list")
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(140, 520, 75, 23))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_connect.setText(_translate("Form", "Connect"))
        self.lineEdit_ip.setText(_translate("Form", "IP girin"))
        self.lineEdit_port.setText(_translate("Form", "Port girin"))
        self.lineEdit_dosya_ismi.setText(_translate("Form", "dosya ismi girin"))
        self.pushButton_dosya_ara.setText(_translate("Form", "dosya ara"))
        self.pushButton.setText(_translate("Form", "indir"))

class MyMainWindow(QtWidgets.QMainWindow, Ui_Form):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        self.setupUi(self)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    ui = MyMainWindow()
    ui.show()
    sys.exit(app.exec_())

