import os
import psycopg2
from datetime import datetime
from typing import Optional, Dict, List, Any
import json

class SaulDatabase:
    """Conexión y operaciones con la base de datos de Saulo"""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL no configurada")
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        return psycopg2.connect(self.db_url)
    
    # ===== ESTADO =====
    def get_user_state(self, user_id: str = "pablo_main") -> Dict[str, Any]:
        """Obtiene el estado actual de Saulo para un usuario"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT current_state, state_counter, last_deep_topic, 
                           total_ontological_exchanges, last_state_change
                    FROM saulo_state 
                    WHERE user_id = %s
                """, (user_id,))
                row = cur.fetchone()
                
                if row:
                    return {
                        "current_state": row[0],
                        "state_counter": row[1],
                        "last_deep_topic": row[2],
                        "total_ontological_exchanges": row[3],
                        "last_state_change": row[4]
                    }
                else:
                    # Crear usuario si no existe
                    self._create_user(user_id)
                    return self.get_user_state(user_id)
    
    def update_state(self, user_id: str, **updates):
        """Actualiza campos del estado de Saulo"""
        if not updates:
            return
            
        fields = []
        values = []
        for key, value in updates.items():
            fields.append(f"{key} = %s")
            values.append(value)
        
        values.append(user_id)
        
        query = f"""
            UPDATE saulo_state 
            SET {', '.join(fields)}, last_state_change = NOW()
            WHERE user_id = %s
            RETURNING current_state
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()
                return cur.fetchone()[0]
    
    def increment_counter(self, user_id: str):
        """Incrementa el contador de ignorancia ontológica"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE saulo_state 
                    SET state_counter = state_counter + 1 
                    WHERE user_id = %s
                    RETURNING state_counter
                """, (user_id,))
                conn.commit()
                return cur.fetchone()[0]
    
    def reset_counter(self, user_id: str):
        """Reinicia el contador de ignorancia ontológica"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE saulo_state 
                    SET state_counter = 0 
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()
    
    # ===== HISTORIAL =====
    def add_message(self, user_id: str, role: str, content: str, 
                   is_ontological: bool = False):
        """Añade un mensaje al historial"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversation_history 
                    (user_id, role, content, is_ontological)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (user_id, role, content, is_ontological))
                conn.commit()
                return cur.fetchone()[0]
    
    def get_recent_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Obtiene el historial reciente de conversación"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT role, content, is_ontological, timestamp
                    FROM conversation_history 
                    WHERE user_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (user_id, limit))
                
                rows = cur.fetchall()
                # Invertir para orden cronológico
                return [
                    {"role": row[0], "content": row[1], 
                     "is_ontological": row[2], "timestamp": row[3]}
                    for row in reversed(rows)
                ]
    
    # ===== INSIGHTS ONTOLÓGICOS =====
    def add_ontological_insight(self, user_id: str, 
                               conversation_excerpt: str,
                               saulos_interpretation: str,
                               primary_category: Optional[str] = None,
                               source_state: str = "base"):
        """Registra un nuevo insight ontológico de Saulo"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ontological_insights 
                    (user_id, conversation_excerpt, saulos_interpretation,
                     primary_category, source_state)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, conversation_excerpt, saulos_interpretation,
                     primary_category, source_state))
                conn.commit()
                
                # Incrementar contador de intercambios ontológicos
                cur.execute("""
                    UPDATE saulo_state 
                    SET total_ontological_exchanges = total_ontological_exchanges + 1,
                        last_deep_topic = %s
                    WHERE user_id = %s
                """, (primary_category or "diálogo profundo", user_id))
                conn.commit()
                
                return cur.fetchone()[0]
    
    def get_ontological_insights(self, user_id: str, 
                                limit: int = 5) -> List[Dict]:
        """Obtiene insights ontológicos recientes"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT primary_category, saulos_interpretation, 
                           timestamp, source_state
                    FROM ontological_insights 
                    WHERE user_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (user_id, limit))
                
                return [
                    {
                        "category": row[0],
                        "interpretation": row[1],
                        "timestamp": row[2],
                        "source_state": row[3]
                    }
                    for row in cur.fetchall()
                ]
    
    # ===== MÉTODOS PRIVADOS =====
    def _create_user(self, user_id: str):
        """Crea un nuevo usuario en el sistema"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO saulo_state (user_id, current_state)
                    VALUES (%s, 'base')
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id,))
                conn.commit()
