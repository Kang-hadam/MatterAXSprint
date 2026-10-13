use std::sync::atomic::Ordering;

use serde::{Deserialize, Serialize};
use vespera::{
    Schema,
    axum::{Json, extract::State},
};

use crate::utils::AppState;

#[derive(Serialize, Deserialize, Schema)]
#[serde(rename_all = "camelCase")]
pub struct DangerStatus {
    pub danger: bool,
}

#[vespera::route(get)]
pub async fn get_danger(State(state): State<AppState>) -> Json<DangerStatus> {
    Json(DangerStatus {
        danger: state.danger.load(Ordering::Relaxed),
    })
}

#[vespera::route(put)]
pub async fn set_danger(
    State(state): State<AppState>,
    Json(status): Json<DangerStatus>,
) -> Json<DangerStatus> {
    state.danger.store(status.danger, Ordering::Relaxed);
    Json(status)
}
