```python
def to_df(self) -> "pd.DataFrame":
    """
    Execute the query and return the results as a pandas DataFrame.
    In addition to the selected columns, LanceDB also returns a vector
    and also the "_distance" column which is the distance between the query
    vector and the returned vector.
    """
    return self.to_arrow().to_pandas()

def to_arrow(self) -> pa.Table:
    """
    Execute the query and return the results as an
    [Apache Arrow Table](https://arrow.apache.org/docs/python/generated/pyarrow.Table.html#pyarrow.Table).

    In addition to the selected columns, LanceDB also returns a vector
    and also the "_distance" column which is the distance between the query
    vector and the returned vectors.
    """
    vector = self._query if isinstance(self._query, list) else self._query.tolist()
    query = Query(
        vector=vector,
        filter=self._where,
        k=self._limit,
        metric=self._metric,
        columns=self._columns,
        nprobes=self._nprobes,
        refine_factor=self._refine_factor,
        vector_column=self._vector_column,
    )
    return self._table._execute_query(query)
def __init__(__pydantic_self__, **data: Any) -> None:
        """
        Create a new model by parsing and validating input data from keyword arguments.

        Raises ValidationError if the input data cannot be parsed to form a valid model.
        """
        # Uses something other than `self` the first arg to allow "self" as a settable attribute
        values, fields_set, validation_error = validate_model(__pydantic_self__.__class__, data)
        if validation_error:
            raise validation_error
        try:
            object_setattr(__pydantic_self__, '__dict__', values)
        except TypeError as e:
            raise TypeError(
                'Model values must be a dict; you may not have returned a dictionary from a root validator'
            ) from e
        object_setattr(__pydantic_self__, '__fields_set__', fields_set)
        __pydantic_self__._init_private_attributes()
```

Here is some relevant Python code, does this help us debug?