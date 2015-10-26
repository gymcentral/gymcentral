
DB Utils Documentation.
=======================


This is the explanation of the class created to manage the DB.

The models are defined in `models.py`

.. note::

    Most of the functions have ``**kwargs`` as final parameter. This because the functions usually calls
    :py:meth:`._APIDB__get` function to get the data (or any of the *support* functions)


.. autoclass:: api_db_utils.APIDB
   :members:
   :private-members:

