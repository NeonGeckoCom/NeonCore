# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

current dev branch

### Added

- added this changelog

 
### Fixed



### Changed

- mycroft backend
    - make use of backend optional
        - skill settings
        - Api class
        - remote config
        - metrics
    
- remove relative imports everywhere
    - improves readability
    - removes dependency on work_dir (allows to run directly from pycharm)
    
    
- mycroft.conf
    - add config option to enable/disable backend usage
    - change default STT to google
    - change data_dir to ~/mycroft_data
        - allow to easily run code without worrying about permissions
   
## [mycroft-16jan2020]

Forked from mycroft

[unreleased]: https://github.com/NeonJarbas/NeonCore/tree/dev
[mycroft-16jan2020]: https://github.com/NeonJarbas/NeonCore/tree/mycroft/16/01/2020
