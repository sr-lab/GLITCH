describe "when locking the chef-client run", :unix_only => true do
    let(:random_temp_root) do
        Kernel.srand(Time.now.to_i + Process.pid)
        "/tmp/#{Kernel.rand(Time.now.to_i + Process.pid)}"
    end
end