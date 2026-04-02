# import pytest
# from fastapi import HTTPException
# from app.services.user_service import UserService

# class MockUser:
#     id = "660abb4f2e3f4a1234567890"

# @pytest.mark.asyncio
# async def test_service_delete_logic(fake_db):
#     service = UserService(fake_db)
#     user_obj = MockUser()
    
#     # 1. Test Failure (User not in DB)
#     with pytest.raises(HTTPException) as exc:
#         await service.delete_user_account(user_obj)
#     assert exc.value.status_code == 404

#     # 2. Test Success (Seed user first)
#     from bson import ObjectId
#     await fake_db["users"].insert_one({"_id": ObjectId(user_obj.id)})
    
#     result = await service.delete_user_account(user_obj)
#     assert result["message"] == "User successfully deleted"
