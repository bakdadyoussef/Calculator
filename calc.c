#include Qapplication
#include Qwidgets
#include Qgridlayout
#include Qpushbutton
#include Qeditline 

class calculator : Public Qwidget {
  Q_object
Public:
  calculator(Qwidget *Parent = nullptr) : Qwidget(Parent) {
