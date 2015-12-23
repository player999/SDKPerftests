import subprocess
import os
import argparse
import sys
import glob
import re
import shutil

SVN="svn.exe"
SEPARATOR="\\"
EXTENSION = "dll"

def svn_export_fromfile(filepath, outdir, uname, passw):
	adds = open(filepath, "r").readlines()
	for entry in adds:
		entry = entry[:-1].split(' ')
		svn_export(entry[0], outdir, uname, passw, entry[1])

def svn_export(in_path, outdir, uname, passw, revision):
	export_path = outdir + SEPARATOR
	if not os.path.exists(export_path):
		os.makedirs(export_path)		
	export_line = "export --force --username %s --password %s -r %s %s %s"%(uname, passw, revision, in_path, export_path)
	args = [SVN]
	args.extend(export_line.split(' '))
	subprocess.call(args)

def svn_export_depends(in_path, outdir, uname, passw):
	export_path = outdir + SEPARATOR + "depends"
	if not os.path.exists(export_path):
		os.makedirs(export_path)
	else:
		shutil.rmtree(export_path)
		os.makedirs(export_path)
	for dpath in in_path:	
		export_line = "export --force --username %s --password %s %s %s"%(uname, dpath, in_path, export_path)
		args = [SVN]
		args.extend(export_line.split(' '))
		subprocess.call(args)
	
def svn_deploy(deploy_path, outdir, svn_user, svn_pass, revision=None):
    path_remote = outdir + SEPARATOR + "deploy_remote"
    path_local = outdir + SEPARATOR  + "deploy"
    shutil.rmtree(path_remote, True)
    checkout_line = "checkout --force --username %s --password %s %s %s"%(svn_user, svn_pass, deploy_path, path_remote)
    print(checkout_line)
    args = [SVN]
    args.extend(checkout_line.split(' '))
    subprocess.call(args)
    for root, dirs, files in os.walk(os.path.abspath(path_local)):
        for fle in  files:
            src_file = root + SEPARATOR + fle
            dst_file = root.replace(path_local, path_remote) + SEPARATOR + fle
            if not os.path.exists(root.replace(path_local, path_remote)):
                os.makedirs(root.replace(path_local, path_remote))
            print(dst_file)
            shutil.copy(src_file, dst_file)
    for root, dirs, files in os.walk(os.path.abspath(path_remote)):
        result = re.search(".svn", root)
        if result != None:
            continue
        for fle in  files:
            add_line = "add %s"%(root + SEPARATOR + fle)
            args = [SVN]
            args.extend(add_line.split(' '))
            subprocess.call(args)
            print(root + SEPARATOR + fle)
    if revision:
        commit_line = "commit -m Revision_%s "%(revision) + path_remote
    else:
        commit_line = "commit -m Release_commit " + path_remote
    args = [SVN]
    args.extend(commit_line.split(' '))
    subprocess.call(args)
    shutil.rmtree(path_remote, True)

def svn_getrevision(path):
	output = subprocess.Popen([SVN, "info", path], stdout=subprocess.PIPE).communicate()[0].decode("ascii")
	match = re.search("Revision: (.*)", output)
	return match.group(1)[:-1]
	
if __name__=="__main__":
	#print(svn_getrevision("https://projector.vit.ua/svn/vodi.releng/vodi/2.4.8/arch/windows.vs2010.release/amd64/libexec/aorp/modules"))
	svn_export_fromfile("svn_config.conf", "outdir", "taras.zakharchenko", "a8f1f5")
	