import enum

class RC(enum.Enum):
    """ This enum represents a standardized way to define return codes """
    OK                      = enum.auto()
    BAD_HTTP_REQUEST        = enum.auto()
    
    NOT_FOUND               = enum.auto()
    INVALID_PARAM_TYPE      = enum.auto()
    
    IO_ERROR                = enum.auto()
    DATABASE_ERROR          = enum.auto()
    
    QUERY_ERROR             = enum.auto()
    ERROR                   = enum.auto()
    
    BAD_PARAM               = enum.auto()

    MYSQL_SERVER_ERROR      = enum.auto()
    MYSQL_CONNECTION_ERROR  = enum.auto()
    
    POSTGRE_SERVER_ERROR      = enum.auto()
    POSTGRE_CONNECTION_ERROR  = enum.auto()

    UNKNOWN_EXCEPTION       = enum.auto()
    CONFIG_ERROR            = enum.auto()
    
    WRONG_DATA_TYPE         = enum.auto()
    BAD_FUNC_RETURN         = enum.auto()
