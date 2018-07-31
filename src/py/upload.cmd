rem Python 3
python setup.py bdist_wheel

rem Python 2.7
rem activete py27
rem python.exe setup.py bdist_wheel
rem deactivate

twine upload dist/*