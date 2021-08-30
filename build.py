# -*- coding: utf-8 -*-
"""
The shared library can also be built manually using the command:
$ cythonize -X language_level=3 -a -i ./iscc_core/cdc.py
$ cythonize -X language_level=3 -a -i ./iscc_core/minhash.py
"""


def build(setup_kwargs):
    try:
        from Cython.Build import cythonize, build_ext

        setup_kwargs.update(
            dict(
                ext_modules=cythonize(["./iscc_core/cdc.py", "./iscc_core/minhash.py"]),
                cmdclass=dict(build_ext=build_ext),
            )
        )
    except Exception as e:
        print(e)
        print("************************************************************")
        print("Cannot compile C accelerator module, use pure python version")
        print("************************************************************")