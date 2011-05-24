import pybedtools
import os, difflib
from nose.tools import assert_raises

testdir = os.path.dirname(__file__)

pybedtools.set_tempdir('.')

def fix(x):
    """
    Replaces spaces with tabs, removes spurious newlines, and lstrip()s each
    line. Makes it really easy to create BED files on the fly for testing and
    checking.
    """
    s = ""
    for i in  x.splitlines():
        i = i.strip()
        if len(i) == 0:
            continue
        i = i.split()
        i = '\t'.join(i)+'\n'
        s += i
    return s

def test_cleanup():
    """
    make sure the tempdir and cleanup work
    """
    assert os.path.abspath(pybedtools.get_tempdir()) == os.path.abspath('.')

    # make a fake tempfile, not created during this pybedtools session
    testfn = 'pybedtools.TESTING.tmp'
    os.system('touch %s' % testfn)
    assert os.path.exists(testfn)

    # make some temp files
    a = pybedtools.BedTool(os.path.join(testdir, 'data', 'a.bed'))
    b = pybedtools.BedTool(os.path.join(testdir, 'data', 'b.bed'))
    c = a.intersect(b)

    # after standard cleanup, c's fn should be gone but the fake one still
    # there...
    pybedtools.cleanup(verbose=True)
    assert os.path.exists(testfn)
    assert not os.path.exists(c.fn)

    # Unless we force the removal of all temp files.
    pybedtools.cleanup(remove_all=True)
    assert not os.path.exists(testfn)

    # a.fn and b.fn better be there still!
    assert os.path.exists(a.fn)
    assert os.path.exists(b.fn)

def test_decorators():
    from pybedtools.helpers import _returns_bedtool, _help

    @_returns_bedtool()
    def dummy():
        pass
    assert "returns a new bedtool instance" in dummy.__doc__

    @_help('intersectBed')
    def dummy2():
        pass

    # "-a" ought to be in the help string for intersectBed somewhere....
    assert '-a' in dummy2.__doc__

def test_bedtools_check():
    # this should run fine (especially since we've already imported pybedtools)
    pybedtools.check_for_bedtools()

    # but this should crap out
    assert_raises(OSError, pybedtools.check_for_bedtools, **dict(program_to_check='nonexistent',))

def test_call():
    tmp = os.path.join(pybedtools.get_tempdir(), 'test.output')
    from pybedtools.helpers import call_bedtools, BEDToolsError
    assert_raises(BEDToolsError, call_bedtools, *(['intersectBe'], tmp))

    pybedtools.set_bedtools_path('nonexistent')
    a = pybedtools.example_bedtool('a.bed')
    assert_raises(OSError, a.intersect, a)
    pybedtools.set_bedtools_path()
    assert a.intersect(a,u=True) == a

def test_chromsizes():
    assert_raises(OSError, pybedtools.get_chromsizes_from_ucsc, 'dm3', mysql='wrong path')
    assert_raises(ValueError, pybedtools.get_chromsizes_from_ucsc, 'dm3', timeout=0)
    try:

        print pybedtools.chromsizes('dm3')
        print pybedtools.get_chromsizes_from_ucsc('dm3')
        assert pybedtools.chromsizes('dm3') == pybedtools.get_chromsizes_from_ucsc('dm3')

        hg17 = pybedtools.chromsizes('hg17')

        assert hg17['chr1'] == (0, 245522847)

        fn = pybedtools.chromsizes_to_file(hg17, fn='hg17.genome')
        expected = 'chr1\t245522847\n'
        results = open(fn).readline()
        print results
        assert expected == results

        # make sure the tempfile version works, too
        fn = pybedtools.chromsizes_to_file(hg17, fn=None)
        expected = 'chr1\t245522847\n'
        results = open(fn).readline()
        print results
        assert expected == results

        assert_raises(OSError,
                      pybedtools.get_chromsizes_from_ucsc, 
                      **dict(genome='hg17', mysql='nonexistent'))

        os.unlink('hg17.genome')
    except OSError:
        sys.stdout.write("mysql error -- test for chromsizes from UCSC didn't run")

def test_ff_center():
    from pybedtools.featurefuncs import center
    a = pybedtools.example_bedtool('a.bed')
    b = a.each(center, width=10)
    expected = fix("""
    chr1	45	55	feature1	0	+
    chr1	145	155	feature2	0	+
    chr1	320	330	feature3	0	-
    chr1	920	930	feature4	0	+""")
    assert str(b) == expected

def test_getting_example_beds():
    assert 'a.bed' in pybedtools.list_example_files()

    a_fn = pybedtools.example_filename('a.bed')
    assert a_fn == os.path.join(testdir, 'data', 'a.bed')

    a = pybedtools.example_bedtool('a.bed')
    assert a.fn == os.path.join(testdir, 'data', 'a.bed')

    # complain appropriately if nonexistent paths are asked for
    assert_raises(ValueError, pybedtools.example_filename, 'nonexistent')
    assert_raises(ValueError, pybedtools.example_bedtool, 'nonexistent')
    assert_raises(ValueError, pybedtools.set_tempdir, 'nonexistent')

def test_help():
    from pybedtools.helpers import _help

    # test support for uninstalled programs
    @_help('nonexistent')
    def dummyfunc():
        return 100
    assert_raises(NotImplementedError, dummyfunc)

    # test invariant return value
    @_help('intersectBed')
    def dummyfunc():
        return 100
    assert dummyfunc() == 100

def teardown():
    # always run this!
    pybedtools.cleanup(remove_all=True)
