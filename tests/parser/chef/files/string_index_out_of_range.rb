def sevenzip_path_from_registry
    begin
        basepath = ::Win32::Registry::HKEY_LOCAL_MACHINE.open('SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\7zFM.exe').read_s('Path')

    # users like pretty errors
    rescue ::Win32::Registry::Error
        raise 'Failed to find the path of 7zip binary by searching checking HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\7zFM.exe\Path. Make sure to install 7zip before using this resource. If 7zip is installed and you still receive this message you can also specify the 7zip binary path by setting node["ark"]["sevenzip_binary"]'
    end
    "#{basepath}7z.exe"
end

https_map = "
    map $scheme $https {
        default off;
        https on;
    }
"