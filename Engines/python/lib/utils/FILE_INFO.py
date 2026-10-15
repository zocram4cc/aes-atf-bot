import os

# Folder paths
EXPORTS_TO_ADD_PATH          = "exports_to_add"
EXTRACTED_TEAMS_PATH         = "extracted_teams"
EXTRACTED_REFEREES_PATH      = "extracted_referees"
PATCHES_CONTENTS_PATH        = "patches_contents"
PATCHES_OUTPUT_PATH          = "patches_output"

# Settings file
SETTINGS_PATH                = os.path.join("settings.ini")

# Team files
TEAMS_LIST_PATH              = "teams_list.txt"
TEAMNOTES_PATH               = "teamnotes.txt"

# Logs
SUGGESTIONS_LOG_PATH         = "suggestions.log"
ISSUES_LOG_PATH              = "issues.log"
CRASH_LOG_PATH               = "crash.log"

# Run batch
RUN_BATCH_PATH               = os.path.join("Engines", "compiler_run.bat")

# State files
STATE_FOLDER_PATH            = os.path.join("Engines", "state")
CHECK_LAST_PATH              = os.path.join(STATE_FOLDER_PATH, "update_check_last.txt")
SKIP_LAST_PATH               = os.path.join(STATE_FOLDER_PATH, "update_skip_last.txt")
ADMIN_WARNED_PATH            = os.path.join(STATE_FOLDER_PATH, "admin_warned.txt")
FIRST_RUN_DONE_PATH          = os.path.join(STATE_FOLDER_PATH, "first_run_done.txt")

# Template files
TEMPLATE_FOLDER_PATH         = os.path.join("Engines", "templates")
DUMMY_MTL_NAME               = "dummy.mtl"
DUMMY_MODEL_NAME             = "oral_dummy_win32.model"
GENERIC_FPKD_NAME            = "generic.fpkd"
KIT_MASK_NAME                = "kit_mask.dds"
FACE_DIFF_BIN_NAME           = "face_diff.bin"

# Refs template paths
REFS_TEMPLATE_PREFOX_PATH    = os.path.join(TEMPLATE_FOLDER_PATH, "refscpk_prefox")
REFS_TEMPLATE_FOX_PATH       = os.path.join(TEMPLATE_FOLDER_PATH, "refscpk_fox")

# Settings tools
SETTINGS_DEFAULT_PATH        = os.path.join(TEMPLATE_FOLDER_PATH, "settings_default.ini")
SETTINGS_TRANSFER_TABLE_PATH = os.path.join(TEMPLATE_FOLDER_PATH, "settings_transfer_table.txt")

# Bin files
BIN_FOLDER_PATH              = os.path.join("Engines", "bins")
TEAMCOLOR_BIN_NAME           = "TeamColor.bin"
UNICOLOR_BIN_NAME            = "UniColor.bin"
UNIPARAM_NAME                = "UniformParameter.bin"
UNIPARAM_18_NAME             = "UniformParameter18.bin"
UNIPARAM_19_NAME             = "UniformParameter19.bin"

# DirectXTex
TEXCONV_PATH                 = os.path.join("Engines", "directxtex", "texconv.exe")
