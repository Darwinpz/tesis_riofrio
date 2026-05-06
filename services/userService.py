import os
from typing import Dict
from werkzeug.utils import secure_filename
from models.userModel import UserModel
from models.personModel import PersonModel
from werkzeug.security import generate_password_hash, check_password_hash
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository
from utils.userUtil import validate_registration_data, validate_login_data

ALLOWED_PHOTO_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

def _allowed_photo(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXT

class UserService:
    #Servicio con lógica de negocio para los usuarios

    @staticmethod
    def create_user(identification: str, first_name: str, last_name: str, email: str, password: str) -> Dict:
        # Crea un nuevo usuario con validaciones

        errors = validate_registration_data(identification, first_name, last_name, email, password)

        if errors:
            return {
                "success": False,
                "message": ", ".join(errors)
            }

        user_id = None
        
        try:
            if UserRepository.exist_by_email(email):
                return {
                    "success": False,
                    "message": "Ya existe un usuario con ese correo electrónico"
                }
            
            if PersonRepository.exist_by_identification(identification):
                return {
                    "success": False,
                    "message": "Ya existe un usuario con esa identificacion"
                }
            
            #Creación del user
            hashed_password = generate_password_hash(password)
            user = UserModel(email, password=hashed_password, role="client")
            user_id = UserRepository.create(user)
            #Creación del person
            person = PersonModel(user_id,identification,first_name,last_name)
            PersonRepository.create(person)

            return {
                "success": True,
                "message": "Usuario creado exitosamente"
            }
        except Exception as e:
            if user_id:
                UserRepository.delete_by_id(user_id)
            return {
                "success": False,
                "message": f"Error al crear el usuario: {e}"
            }
        
    @staticmethod
    def get_all_users() -> Dict:
        #Obtiene todos los usuarios

        users = UserRepository.find_all()
        
        return{
            "users": users
        }
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Dict:
        #Obtener usuario por id
        try:

            user = UserRepository.find_by_id(user_id)
            if not user:
                return{
                    "success": False,
                    "message": "Usuario no encontrado"
                }
            person = PersonRepository.find_by_user_id(user_id)

            profile = {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "identification": person.identification if person else "",
                "first_name": person.first_name if person else "",
                "last_name": person.last_name if person else "",
                "phone": person.phone if person else None,
                "photo_path": person.photo_path if person else None
            }

            return {
                "success": True,
                "message": "Usuario encontrado",
                "user": profile
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al buscar el usuario: {e}"
            }
    
    @staticmethod
    def get_all_users_with_profile() -> Dict:
        try:
            users = UserRepository.find_all()
            profiles = []
            for user in users:
                person = PersonRepository.find_by_user_id(user.id)
                profiles.append({
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "first_name": person.first_name if person else "",
                    "last_name": person.last_name if person else "",
                    "identification": person.identification if person else "",
                    "phone": person.phone if person else "",
                    "photo_path": person.photo_path if person else None,
                    "created_at": user.created_at
                })
            return {"success": True, "users": profiles}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener usuarios: {e}"}

    @staticmethod
    def update_profile(user_id: str, first_name: str, last_name: str, phone: str) -> Dict:
        if not first_name or not first_name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        if not last_name or not last_name.strip():
            return {"success": False, "message": "El apellido es obligatorio"}
        try:
            PersonRepository.update_by_user_id(user_id, {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "phone": phone.strip() if phone else None
            })
            return {"success": True, "message": "Perfil actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar el perfil: {e}"}

    @staticmethod
    def update_photo(user_id: str, photo_file, upload_folder: str) -> Dict:
        if not photo_file or not photo_file.filename:
            return {"success": False, "message": "No se seleccionó ninguna imagen"}
        if not _allowed_photo(photo_file.filename):
            return {"success": False, "message": "Formato de imagen no permitido (usa png, jpg, jpeg)"}
        try:
            filename = secure_filename(f"{user_id}_{photo_file.filename}")
            save_path = os.path.join(upload_folder, filename)
            photo_file.save(save_path)
            photo_path = f"uploads/perfiles/{filename}"
            PersonRepository.update_by_user_id(user_id, {"photo_path": photo_path})
            return {"success": True, "message": "Foto de perfil actualizada", "photo_path": photo_path}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar la foto: {e}"}

    @staticmethod
    def update_user_role(user_id: str, role: str) -> Dict:
        if role not in ("admin", "operator", "client"):
            return {"success": False, "message": "Rol inválido"}
        try:
            if not UserRepository.find_by_id(user_id):
                return {"success": False, "message": "Usuario no encontrado"}
            UserRepository.update_role(user_id, role)
            return {"success": True, "message": "Rol actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar el rol: {e}"}

    @staticmethod
    def delete_user(user_id: str) -> Dict:
        try:
            if not UserRepository.find_by_id(user_id):
                return {"success": False, "message": "Usuario no encontrado"}
            PersonRepository.delete_by_user_id(user_id)
            UserRepository.delete_by_id(user_id)
            return {"success": True, "message": "Usuario eliminado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar el usuario: {e}"}

    @staticmethod
    def get_clients() -> Dict:
        try:
            users = UserRepository.find_by_role("client")
            clients = []
            for user in users:
                person = PersonRepository.find_by_user_id(user.id)
                clients.append({
                    "id": user.id,
                    "email": user.email,
                    "full_name": f"{person.first_name} {person.last_name}" if person else user.email
                })
            return {"success": True, "clients": clients}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener clientes: {e}"}

    @staticmethod
    def login_user(email: str, password: str) -> Dict:
        #Flujo de autenticación

        errors = validate_login_data(email, password)

        if errors:
            return {
                "success": False,
                "message": ", ".join(errors)
            }

        try:
            
            user = UserRepository.find_by_email(email)

            if not user:
                return {
                    "success": False,
                    "message": "Email no existente"
                }
            if not check_password_hash(user.password, password):
                return {
                    "success": False,
                    "message": "Contraseña incorrecta"
                }
            return{
                "success": True,
                "message": "Inicio de sesión exitoso",
                "user_id": user.id
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al iniciar sesión: {e}"
            }