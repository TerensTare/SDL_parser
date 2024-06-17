
(
    (comment) @function.docs
    .
    (declaration
        (storage_class_specifier)
        type: (_) @function.return
        declarator: (function_declarator
            declarator: (identifier) @function.name
            parameters: (parameter_list) @function.params
        )
    ) @function.decl
) @function

(
    (comment) @function.docs
    .
    (declaration
        (storage_class_specifier)
        type: (_) @function.return
        declarator: (pointer_declarator
            declarator: (function_declarator
                declarator: (identifier) @function.name
                parameters: (parameter_list) @function.params
            )
        ) @function.return_ptr
    ) @function.decl
) @function

(type_definition
    type: (_) @callback.return
    declarator: (function_declarator
        declarator: (parenthesized_declarator
            (pointer_declarator declarator: (_) @callback.name)
        )
        parameters: (parameter_list) @callback.params
    )
) @callback

(type_definition
	type: (_) @callback.return
    declarator: (pointer_declarator
        declarator: (function_declarator
            declarator: (parenthesized_declarator
                (pointer_declarator declarator: (_) @callback.name)
            )
            parameters: (parameter_list) @callback.params
        )
     ) @callback.return_ptr
) @callback

(type_definition
    type: (struct_specifier !body) @opaque
    declarator: (type_identifier) @opaque.name
)

(type_definition
    type: [
        (enum_specifier
            name: (type_identifier) @enum.name
            body: (enumerator_list) @enum.entries
        ) @enum
        (struct_specifier
            name: (type_identifier) @struct.name
            body: (field_declaration_list) @struct.members
        ) @struct
        (union_specifier
            name: (type_identifier) @union.name
            body: (field_declaration_list) @union.members
        ) @union
    ]
)

(
    (type_definition
        type: [
            (type_identifier)
            (primitive_type)
            (sized_type_specifier)
        ] @bitflag.type
        declarator: (type_identifier) @bitflag.name
    )
    . [
        (preproc_function_def)
        (preproc_def
            name: (_) @flag.name
            value: (_) @flag.value
        ) @flag
    ]+
) @bitflag

(preproc_function_def
    name: (_) @fn_macro.name
    parameters: (_) @fn_macro.params
    value: (_) @fn_macro.body
) @fn_macro

(type_definition
    type: [ (type_identifier) (primitive_type) ] @alias.type
    declarator: [
        (type_identifier) @alias.name
        (pointer_declarator
            (type_identifier) @alias.name
        ) @alias.ptr
    ]
) @alias

(preproc_def name: (_) @const.name value: (_) @const.value) @const

