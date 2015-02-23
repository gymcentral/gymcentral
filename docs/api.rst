
API Documentation.
==================

This is the explanation of the api.

.. note::

    The URL of the app are:
        - ``COACH_URL = /api/coach``
        - ``TRAINEE_URL = /api/trainee``

    ``uskey_`` stands for UrlSafe Key. The UrlSafe Key is the value passed as ``id`` in the responses.


.. warning::

    For ``PUT`` or for generally every API call that **updates** a resource the following assumptions are valid:

        - Partial update works (no need to specify all the fields)
        - do **NOT** send reserved fields: 'id', 'key', 'namespace', 'parent'
        - do **NOT** use the call to create a new object (this is against REST, I know)

.. automodule:: api
    :members:
    :exclude-members: GCApp