#!/usr/bin/env python
"""
Script to explore PhonePe SDK structure
"""
try:
    import phonepe
    print("PhonePe module imported successfully")
    print("PhonePe version:", getattr(phonepe, '__version__', 'Unknown'))
    
    try:
        from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
        print("StandardCheckoutClient imported successfully")
    except Exception as e:
        print(f"Error importing StandardCheckoutClient: {e}")
    
    try:
        from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
        print("StandardCheckoutPayRequest imported successfully")
    except Exception as e:
        print(f"Error importing StandardCheckoutPayRequest: {e}")
    
    try:
        from phonepe.sdk.pg.env import Env
        print("Env imported successfully")
        print("Env options:", [attr for attr in dir(Env) if not attr.startswith('_')])
    except Exception as e:
        print(f"Error importing Env: {e}")
    
    # Try to find exceptions
    try:
        import phonepe.sdk.pg as pg
        print("PG module dir:", [attr for attr in dir(pg) if not attr.startswith('_')])
        
        # Try common exception patterns
        try:
            from phonepe.sdk.pg.common.exception import PhonePeException
            print("PhonePeException found in common.exception")
        except:
            pass
            
        try:
            from phonepe.sdk.pg.payments.v2.exceptions import PhonePeException
            print("PhonePeException found in payments.v2.exceptions")
        except:
            pass
            
        try:
            from phonepe.sdk.pg.exception import PhonePeException
            print("PhonePeException found in exception")
        except:
            pass
            
        try:
            from phonepe.sdk.exception import PhonePeException
            print("PhonePeException found in sdk.exception")
        except:
            pass
            
    except Exception as e:
        print(f"Error exploring PG module: {e}")
        
except Exception as e:
    print(f"Error importing phonepe: {e}")
