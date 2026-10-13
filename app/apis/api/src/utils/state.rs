use std::sync::{Arc, atomic::AtomicBool};

use crate::config::Config;

#[derive(Clone)]
pub struct AppState {
    pub db: sea_orm::DatabaseConnection,
    pub config: Config,
    // shortcut: 메모리에만 있어 서버 재시작 시 false로 돌아감, 위험 이력이 필요해지면 DB 테이블로 옮길 것
    pub danger: Arc<AtomicBool>,
}
