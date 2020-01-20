class ObjectDB:
    '''A queryable database of wl.Objects'''

    def create_object(self, time, parent, obj_id, type_name):
        '''Create a new objects and add it to the database
        time: str, the time to create the object with
        parent: wl.Object, the object that created this object
        obj_id: int, the ID for the new object
        type_name: str, the Wayland type (such as 'wl_pointer')
        Returns: the newly created object
        '''
        raise NotImplementedError()

    def retrieve_object(self, id, generation, type_name):
        '''Get an object
        id: int, the objects's Wayland ID (database can contain multiple objects with the same ID)
        generation: int or None, 0 for first object with the given ID, 1 for 2nd, -1 for the last, etc
        type_name: str or None, if set, is used to make sure the object is correct, wildcards allowed
        Returns: wl.Object
        Raises: RuntimeError if id or generation is invalid, or type_name is not None and doesn't match object's type
        '''
        raise NotImplementedError()

    def wl_display(self):
        '''Get the wl_display object every connection has'''
        raise NotImplementedError()
